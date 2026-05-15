#!/usr/bin/env python3
"""文件上传服务器 - 支持手机浏览器上传文件到电脑"""

import os
import html
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
import argparse

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件上传</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: 40px auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            padding: 24px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 8px; }
        .header p { opacity: 0.8; font-size: 14px; }
        .body { padding: 24px; }
        .drop-zone {
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            background: #fafafa;
            transition: all 0.3s;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #4f46e5;
            background: #eef2ff;
        }
        .drop-zone p { color: #666; margin-bottom: 10px; }
        .drop-zone .icon { font-size: 48px; margin-bottom: 10px; }
        #fileInput { display: none; }
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(79,70,229,0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .file-list { margin-top: 24px; }
        .file-list h3 { font-size: 16px; margin-bottom: 12px; color: #333; }
        .file-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .file-item span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .file-item a { color: #4f46e5; text-decoration: none; font-size: 14px; margin-right: 10px; }
        .file-item .size { color: #888; font-size: 12px; white-space: nowrap; }
        .alert {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        .alert.success { background: #dcfce7; color: #166534; }
        .alert.error { background: #fee2e2; color: #991b1b; }
        .empty { text-align: center; color: #999; padding: 20px; }
        .progress { display: none; margin-top: 12px; }
        .progress-bar {
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4f46e5, #7c3aed);
            width: 0%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📤 文件上传</h1>
            <p>从手机上传文件到电脑</p>
        </div>
        <div class="body">
            {ALERT}
            <form id="uploadForm" method="post" enctype="multipart/form-data" action="/upload">
                <div class="drop-zone" id="dropZone">
                    <div class="icon">📁</div>
                    <p>点击选择文件或拖放文件</p>
                    <input type="file" name="file" id="fileInput" multiple>
                </div>
                <div class="progress" id="progress">
                    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                </div>
                <button type="submit" class="btn" id="submitBtn" disabled>上传选中文件</button>
            </form>
            <div class="file-list">
                <h3>已上传 ({COUNT} 个文件)</h3>
                <div id="fileList">{FILE_LIST}</div>
            </div>
        </div>
    </div>
    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const submitBtn = document.getElementById('submitBtn');
        const form = document.getElementById('uploadForm');
        const progress = document.getElementById('progress');
        const progressFill = document.getElementById('progressFill');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            fileInput.files = e.dataTransfer.files;
            updateFileCount();
        });
        fileInput.addEventListener('change', updateFileCount);

        function updateFileCount() {
            const count = fileInput.files.length;
            submitBtn.disabled = count === 0;
            submitBtn.textContent = count ? `上传 ${count} 个文件` : '上传选中文件';
        }

        form.addEventListener('submit', e => {
            e.preventDefault();
            const formData = new FormData(form);
            progress.style.display = 'block';
            submitBtn.disabled = true;
            submitBtn.textContent = '上传中...';

            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', e => {
                if (e.lengthComputable) progressFill.style.width = (e.loaded / e.total * 100) + '%';
            });
            xhr.addEventListener('load', () => {
                window.location.href = xhr.responseURL;
            });
            xhr.send(formData);
        });
    </script>
</body>
</html>
"""


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_html()
        elif self.path.startswith("/uploads/"):
            super().do_GET()
        elif self.path == "/api/files":
            self.send_json()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/upload":
            length = int(self.headers.get("Content-Length", 0))
            content_type = self.headers.get("Content-Type", "")
            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[-1].encode()
                data = self.rfile.read(length)
                self._parse_and_save(data, boundary)
                return
        self.send_error(400)

    def send_html(self):
        files = self._get_files()
        alert = ""
        if "?ok=1" in self.path:
            alert = '<div class="alert success">✅ 文件上传成功！</div>'
        elif "?err=1" in self.path:
            alert = '<div class="alert error">❌ 上传失败，请重试</div>'

        file_list_html = ""
        if files:
            for f in files:
                size = format_size(f["size"])
                file_list_html += f"""
                    <div class="file-item">
                        <span title="{html.escape(f['name'])}">{html.escape(f['name'])}</span>
                        <span class="size">{size}</span>
                    </div>
                """
        else:
            file_list_html = '<div class="empty">暂无文件</div>'

        body = (
            HTML.replace("{ALERT}", alert)
            .replace("{COUNT}", str(len(files)))
            .replace("{FILE_LIST}", file_list_html)
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def send_json(self):
        files = self._get_files()
        import json

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(files).encode())

    def _get_files(self):
        files = []
        if os.path.exists(UPLOAD_DIR):
            for name in sorted(os.listdir(UPLOAD_DIR), key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)), reverse=True):
                path = os.path.join(UPLOAD_DIR, name)
                if os.path.isfile(path):
                    files.append({"name": name, "size": os.path.getsize(path)})
        return files

    def _parse_and_save(self, data, boundary):
        parts = data.split(b"--" + boundary)
        saved = False
        for part in parts:
            if b"filename=" in part:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                header = part[:header_end].decode(errors="ignore")
                rest = part[header_end + 4 :]
                content = rest.rstrip(b"\r\n").rstrip(b"--\r\n")

                if "filename=" not in header:
                    continue

                name = header.split('filename="')[1].split('"')[0]
                if not name or not content:
                    continue

                # 避免覆盖
                path = os.path.join(UPLOAD_DIR, name)
                if os.path.exists(path):
                    base, ext = os.path.splitext(name)
                    i = 1
                    while os.path.exists(path):
                        path = os.path.join(UPLOAD_DIR, f"{base}_{i}{ext}")
                        i += 1

                with open(path, "wb") as f:
                    f.write(content)
                saved = True
                break

        self.send_response(302)
        self.send_header("Location", "/?ok=1" if saved else "/?err=1")
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main():
    import socket

    parser = argparse.ArgumentParser(description="文件上传服务器")
    parser.add_argument("-p", "--port", type=int, default=8000, help="端口号 (默认 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    args = parser.parse_args()

    # 获取本机 IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()

    server = HTTPServer((args.host, args.port), Handler)
    print(f"\n  ✅ 文件上传服务已启动！")
    print(f"  📱 手机浏览器访问: http://{local_ip}:{args.port}")
    print(f"  📁 上传文件保存位置: {UPLOAD_DIR}")
    print(f"  ⏹️  按 Ctrl+C 停止服务\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
