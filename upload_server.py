#!/usr/bin/env python3
import html
import json
import os
import secrets
import tempfile
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

HOST = os.environ.get("UPLOAD_HOST", "0.0.0.0")
PORT = int(os.environ.get("UPLOAD_PORT", "8000"))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads")).resolve()
MAX_UPLOAD_SIZE = 100 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
AUTH_TOKEN = os.environ.get("FILE_TRANSFER_TOKEN") or secrets.token_urlsafe(32)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def now_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat()


def sanitize_filename(filename: str) -> str:
    filename = unquote(filename or "")
    filename = filename.replace("\\", "/")
    filename = os.path.basename(filename)
    filename = os.path.normpath(filename)

    if filename in {"", ".", ".."}:
        raise ValueError("invalid filename")

    cleaned = []
    forbidden = set('/\\<>:"|?*\x00')
    extra_xss = set("&'`")

    for ch in filename:
        code = ord(ch)
        if code < 32 or code == 127:
            continue
        if ch in forbidden or ch in extra_xss:
            cleaned.append("_")
        else:
            cleaned.append(ch)

    safe_name = "".join(cleaned).strip().strip(".")
    if not safe_name:
        raise ValueError("invalid filename")

    return safe_name[:255]


def resolve_storage_path(filename: str) -> tuple[str, Path]:
    safe_name = sanitize_filename(filename)
    candidate = (UPLOAD_DIR / safe_name).resolve()

    try:
        if os.path.commonpath([str(UPLOAD_DIR), str(candidate)]) != str(UPLOAD_DIR):
            raise ValueError("path traversal")
    except ValueError:
        raise ValueError("path traversal") from None

    return safe_name, candidate


class UploadHandler(BaseHTTPRequestHandler):
    server_version = "SecureFileTransfer/1.0"

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, data, "application/json; charset=utf-8")

    def _send_html(self, status: int, html_text: str) -> None:
        self._send_bytes(status, html_text.encode("utf-8"), "text/html; charset=utf-8")

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"ok": False, "message": message})

    def _request_token(self) -> str:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:].strip()

        header_token = self.headers.get("X-Auth-Token", "")
        if header_token:
            return header_token.strip()

        query = parse_qs(urlparse(self.path).query)
        return (query.get("token", [""])[0] or "").strip()

    def _require_auth(self) -> bool:
        token = self._request_token()
        if not token or not secrets.compare_digest(token, AUTH_TOKEN):
            self._send_error_json(HTTPStatus.UNAUTHORIZED, "Authentication failed.")
            return False
        return True

    def _content_length(self) -> int:
        raw = self.headers.get("Content-Length", "")
        if not raw:
            raise ValueError("missing content length")
        size = int(raw)
        if size < 0:
            raise ValueError("invalid content length")
        return size

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            if not self._require_auth():
                return
            self._send_html(HTTPStatus.OK, self._render_index())
            return

        if parsed.path == "/api/files":
            if not self._require_auth():
                return
            self._handle_list_files()
            return

        if parsed.path == "/download":
            if not self._require_auth():
                return
            self._handle_download()
            return

        self._send_error_json(HTTPStatus.NOT_FOUND, "Request failed.")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/upload":
            if not self._require_auth():
                return
            self._handle_upload()
            return

        self._send_error_json(HTTPStatus.NOT_FOUND, "Request failed.")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/delete":
            if not self._require_auth():
                return
            self._handle_delete()
            return

        self._send_error_json(HTTPStatus.NOT_FOUND, "Request failed.")

    def _handle_list_files(self) -> None:
        items = []
        try:
            for entry in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.name.lower()):
                if not entry.is_file():
                    continue
                stat = entry.stat()
                items.append(
                    {
                        "name": entry.name,
                        "size": stat.st_size,
                        "modifiedAt": now_iso(stat.st_mtime),
                    }
                )
        except OSError:
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "File operation failed.")
            return

        self._send_json(HTTPStatus.OK, {"ok": True, "files": items})

    def _handle_upload(self) -> None:
        raw_name = self.headers.get("X-Filename", "")
        if not raw_name:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Invalid request.")
            return

        try:
            file_size = self._content_length()
            if file_size > MAX_UPLOAD_SIZE:
                self._send_error_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request rejected.")
                return

            safe_name, target_path = resolve_storage_path(raw_name)

            fd, temp_path_str = tempfile.mkstemp(prefix=".upload-", suffix=".tmp", dir=str(UPLOAD_DIR))
            temp_path = Path(temp_path_str)

            written = 0
            try:
                with os.fdopen(fd, "wb") as tmp:
                    remaining = file_size
                    while remaining > 0:
                        chunk = self.rfile.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            raise IOError("incomplete upload")
                        written += len(chunk)
                        if written > MAX_UPLOAD_SIZE:
                            raise IOError("size limit exceeded")
                        tmp.write(chunk)
                        remaining -= len(chunk)
                    tmp.flush()
                    os.fsync(tmp.fileno())

                if written != file_size:
                    raise IOError("size mismatch")

                os.replace(temp_path, target_path)
            except Exception:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

        except ValueError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Invalid request.")
            return
        except OSError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "File operation failed.")
            return
        except Exception:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Request failed.")
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "file": {
                    "name": safe_name,
                    "size": written,
                },
            },
        )

    def _handle_download(self) -> None:
        try:
            query = parse_qs(urlparse(self.path).query)
            raw_name = query.get("file", [""])[0]
            _, path = resolve_storage_path(raw_name)

            if not path.is_file():
                self._send_error_json(HTTPStatus.NOT_FOUND, "Request failed.")
                return

            file_size = path.stat().st_size
            download_name = quote(path.name)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(file_size))
            self.send_header(
                "Content-Disposition",
                f"attachment; filename*=UTF-8''{download_name}",
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            with path.open("rb") as fh:
                while True:
                    chunk = fh.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (ValueError, OSError):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "File operation failed.")
        except Exception:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Request failed.")

    def _handle_delete(self) -> None:
        try:
            query = parse_qs(urlparse(self.path).query)
            raw_name = query.get("file", [""])[0]
            _, path = resolve_storage_path(raw_name)

            if not path.is_file():
                self._send_error_json(HTTPStatus.NOT_FOUND, "Request failed.")
                return

            path.unlink()
        except (ValueError, OSError):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "File operation failed.")
            return

        self._send_json(HTTPStatus.OK, {"ok": True})

    def _render_index(self) -> str:
        token = html.escape(AUTH_TOKEN, quote=True)
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)

        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>File Transfer</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffdf8;
      --line: #d9d0c3;
      --ink: #1d1d1b;
      --accent: #17624a;
      --danger: #a33a2b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #efe4cf 0, transparent 35%),
        linear-gradient(180deg, #f8f4ec 0%, var(--bg) 100%);
    }}
    .wrap {{
      max-width: 880px;
      margin: 40px auto;
      padding: 24px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.05);
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    p {{ margin: 0 0 16px; color: #534c43; }}
    .toolbar {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }}
    input[type=file] {{
      flex: 1;
      min-width: 220px;
    }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font-size: 14px;
    }}
    button.delete {{
      background: var(--danger);
    }}
    button:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    .status {{
      min-height: 24px;
      margin-bottom: 16px;
      color: #534c43;
    }}
    .file-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }}
    .file-item {{
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 12px;
      align-items: center;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
    }}
    .meta {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }}
    .name {{
      font-weight: 600;
      word-break: break-all;
    }}
    .sub {{
      font-size: 13px;
      color: #6d655b;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    @media (max-width: 640px) {{
      .file-item {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>文件传输</h1>
      <p>单文件大小限制 {max_mb}MB。</p>

      <div class="toolbar">
        <input id="fileInput" type="file">
        <button id="uploadBtn">上传</button>
      </div>

      <div id="status" class="status"></div>
      <ul id="fileList" class="file-list"></ul>
    </div>
  </div>

  <script>
    const token = "{token}";
    const maxSize = {MAX_UPLOAD_SIZE};
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadBtn");
    const statusEl = document.getElementById("status");
    const fileList = document.getElementById("fileList");

    function setStatus(message) {{
      statusEl.textContent = message;
    }}

    function formatSize(bytes) {{
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
      return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }}

    async function api(url, options = {{}}) {{
      const res = await fetch(url, {{
        ...options,
        headers: {{
          ...(options.headers || {{}}),
          "X-Auth-Token": token
        }}
      }});
      const data = await res.json().catch(() => ({{ ok: false, message: "Request failed." }}));
      if (!res.ok || !data.ok) {{
        throw new Error(data.message || "Request failed.");
      }}
      return data;
    }}

    async function loadFiles() {{
      try {{
        const data = await api("/api/files");
        fileList.textContent = "";

        for (const file of data.files) {{
          const li = document.createElement("li");
          li.className = "file-item";

          const meta = document.createElement("div");
          meta.className = "meta";

          const name = document.createElement("div");
          name.className = "name";
          name.textContent = file.name;

          const sub = document.createElement("div");
          sub.className = "sub";
          sub.textContent = `${{formatSize(file.size)}} · ${{new Date(file.modifiedAt).toLocaleString()}}`;

          meta.appendChild(name);
          meta.appendChild(sub);

          const link = document.createElement("a");
          link.textContent = "下载";
          link.href = `/download?file=${{encodeURIComponent(file.name)}}&token=${{encodeURIComponent(token)}}`;

          const del = document.createElement("button");
          del.className = "delete";
          del.textContent = "删除";
          del.addEventListener("click", async () => {{
            try {{
              setStatus("处理中...");
              await api(`/delete?file=${{encodeURIComponent(file.name)}}`, {{ method: "DELETE" }});
              setStatus("删除完成。");
              await loadFiles();
            }} catch (err) {{
              setStatus(err.message);
            }}
          }});

          li.appendChild(meta);
          li.appendChild(link);
          li.appendChild(del);
          fileList.appendChild(li);
        }}

        if (!data.files.length) {{
          const empty = document.createElement("li");
          empty.className = "file-item";
          empty.textContent = "暂无文件";
          fileList.appendChild(empty);
        }}
      }} catch (err) {{
        setStatus(err.message);
      }}
    }}

    uploadBtn.addEventListener("click", async () => {{
      const file = fileInput.files[0];
      if (!file) {{
        setStatus("请选择文件。");
        return;
      }}
      if (file.size > maxSize) {{
        setStatus("文件超过大小限制。");
        return;
      }}

      uploadBtn.disabled = true;
      try {{
        setStatus("上传中...");
        await api("/upload", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/octet-stream",
            "X-Filename": encodeURIComponent(file.name)
          }},
          body: file
        }});
        fileInput.value = "";
        setStatus("上传完成。");
        await loadFiles();
      }} catch (err) {{
        setStatus(err.message);
      }} finally {{
        uploadBtn.disabled = false;
      }}
    }});

    loadFiles();
  </script>
</body>
</html>"""


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), UploadHandler)
    print(f"Serving on http://{HOST}:{PORT}")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Auth token: {AUTH_TOKEN}")
    server.serve_forever()


if __name__ == "__main__":
    main()