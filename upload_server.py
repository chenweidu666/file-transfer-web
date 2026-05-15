#!/usr/bin/env python3
"""文件上传服务器 — 手机浏览器传文件到电脑"""

import os
import json
import time
import sqlite3
import html
import socket
import uuid
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import argparse
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "upload.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── SQLite ────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            size INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def add_record(conn, name, size):
    rid = uuid.uuid4().hex[:12]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO uploads VALUES (?,?,?,?)", (rid, name, size, ts))
    conn.commit()
    return rid


def get_records(conn):
    rows = conn.execute(
        "SELECT id, name, size, uploaded_at FROM uploads ORDER BY uploaded_at DESC"
    ).fetchall()
    return [{"id": r[0], "name": r[1], "size": r[2], "uploaded_at": r[3]} for r in rows]


def delete_record(conn, rid):
    conn.execute("DELETE FROM uploads WHERE id = ?", (rid,))
    conn.commit()


def clear_records(conn):
    conn.execute("DELETE FROM uploads")
    conn.commit()


# ── HTML templates ────────────────────────────────────────

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>文件上传</title>
  <style>
    :root { --primary: #4f46e5; --bg: #f1f5f9; --card: #fff; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); padding: 16px; }
    .wrap { max-width: 520px; margin: 0 auto; }

    /* upload card */
    .card { background: var(--card); border-radius: 14px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 16px; }
    .card h2 { font-size: 18px; margin-bottom: 16px; }

    .drop { border: 2px dashed #cbd5e1; border-radius: 12px; padding: 28px 16px; text-align: center; cursor: pointer; transition: .2s; background: #f8fafc; }
    .drop:hover, .drop.over { border-color: var(--primary); background: #eef2ff; }
    .drop input { display: none; }
    .drop p { color: #64748b; margin-top: 8px; font-size: 14px; }

    .btn { display: block; width: 100%; padding: 13px; background: var(--primary); color: #fff; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; margin-top: 14px; cursor: pointer; }
    .btn:disabled { opacity: .5; }

    .bar { display: none; margin-top: 12px; }
    .bar-track { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; width: 0; background: var(--primary); border-radius: 4px; transition: width .15s; }
    .bar-text { text-align: center; font-size: 13px; color: #64748b; margin-top: 4px; }

    /* history */
    .hist { margin-top: 8px; }
    .hist-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .hist-head h3 { font-size: 16px; }
    .hist-head button { font-size: 12px; color: #94a3b8; background: none; border: none; cursor: pointer; }

    .row { display: flex; align-items: center; padding: 10px 12px; background: #f8fafc; border-radius: 10px; margin-bottom: 6px; gap: 8px; }
    .row .info { flex: 1; min-width: 0; }
    .row .fname { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .row meta { display: block; font-size: 12px; color: #94a3b8; }
    .row .dl { color: var(--primary); font-size: 13px; text-decoration: none; }
    .row .del { background: none; border: none; color: #ef4444; font-size: 18px; cursor: pointer; padding: 0 4px; }
    .empty { text-align: center; color: #94a3b8; padding: 20px 0; font-size: 14px; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h2>📤 上传文件</h2>
    <form id="form">
      <div class="drop" id="drop">
        <span style="font-size:36px">📁</span>
        <p>点我选择 或 拖放文件</p>
        <input type="file" id="file" multiple>
      </div>
      <div class="bar" id="bar">
        <div class="bar-track"><div class="bar-fill" id="fill"></div></div>
        <div class="bar-text" id="btext">0%</div>
      </div>
      <button type="submit" class="btn" id="btn" disabled>上传选中文件</button>
    </form>
  </div>

  <div class="card">
    <div class="hist">
      <div class="hist-head">
        <h3>📋 上传记录</h3>
        <button id="clearBtn">清空记录</button>
      </div>
      <div id="list"><div class="empty">暂无记录</div></div>
    </div>
  </div>
</div>

<script>
const drop=document.getElementById('drop'),file=document.getElementById('file'),
      form=document.getElementById('form'),btn=document.getElementById('btn'),
      bar=document.getElementById('bar'),fill=document.getElementById('fill'),
      btext=document.getElementById('btext'),list=document.getElementById('list'),
      clearBtn=document.getElementById('clearBtn');

drop.onclick=()=>file.click();
drop.ondragover=e=>{e.preventDefault();drop.classList.add('over')};
drop.ondragleave=()=>drop.classList.remove('over');
drop.ondrop=e=>{e.preventDefault();drop.classList.remove('over');file.files=e.dataTransfer.files;upd()};
file.onchange=upd;
function upd(){const n=file.files.length;btn.disabled=!n;btn.textContent=n?`上传 ${n} 个文件`:'上传选中文件'}

form.onsubmit=e=>{e.preventDefault();if(!file.files.length)return;
  bar.style.display='block';btn.disabled=true;btn.textContent='上传中...';fill.style.width='0%';
  const fd=new FormData();for(const f of file.files) fd.append('file',f,f.name);
  const xhr=new XMLHttpRequest();
  xhr.open('POST','/upload');
  xhr.upload.onprogress=ev=>{if(ev.lengthComputable){const p=Math.round(ev.loaded/ev.total*100);fill.style.width=p+'%';btext.textContent=p+'%'}};
  xhr.onload=()=>{bar.style.display='none';file.value='';upd();loadHist()};
  xhr.send(fd)};

clearBtn.onclick=()=>{if(confirm('确定清空所有记录？'))fetch('/api/clear',{method:'POST'}).then(loadHist)};

function fmtSize(b){const u=['B','KB','MB','GB'];let i=0;let s=b;while(s>=1024&&i<u.length-1){s/=1024;i++}return(s%1?toFixed(1):s)+' '+u[i]}
function loadHist(){fetch('/api/history').then(r=>r.json()).then(rows=>{
  if(!rows.length){list.innerHTML='<div class="empty">暂无记录</div>';return}
  list.innerHTML=rows.map(r=>{
    const n=r.name.replace(/'/g,"\\'"),m=fmtSize(r.size);
    return(`<div class="row" id="r-${r.id}"><div class="info"><div class="fname" title="${n}">${n}</div><meta>${r.uploaded_at} · ${m}</meta></div><a class="dl" href="/uploads/${encodeURIComponent(r.name)}">下载</a><button class="del" onclick="del('${r.id}')">✕</button></div>`)
  }).join('')
})}
window.del=function(id){fetch('/api/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(loadHist)};
loadHist();
</script>
</body>
</html>
"""


# ── Handler ────────────────────────────────────────────────

class Handler(SimpleHTTPRequestHandler):
    db = None  # shared connection

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/history":
            rows = get_records(self.db)
            data = json.dumps(rows).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/uploads/"):
            super().do_GET()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/upload":
            self._upload()
        elif self.path == "/api/delete":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            delete_record(self.db, body["id"])
            self._empty(200)
        elif self.path == "/api/clear":
            clear_records(self.db)
            self._empty(200)
        else:
            self.send_error(404)

    def _upload(self):
        length = int(self.headers.get("Content-Length", 0))
        ct = self.headers.get("Content-Type", "")

        if "boundary=" not in ct:
            self._empty(400)
            return

        boundary = ct.split("boundary=")[-1].encode()
        data = self.rfile.read(length)
        parts = data.split(b"--" + boundary)

        for part in parts:
            idx = part.find(b"\r\n\r\n")
            if idx == -1:
                continue
            header = part[:idx].decode(errors="ignore")

            if 'filename="' not in header:
                continue

            fname = header.split('filename="')[1].split('"')[0]
            if not fname:
                continue

            content = part[idx + 4:].rstrip(b"\r\n").rstrip(b"--\r\n")
            if not content:
                continue

            # 避免覆盖
            path = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(path):
                base, ext = os.path.splitext(fname)
                i = 1
                while os.path.exists(path):
                    path = os.path.join(UPLOAD_DIR, f"{base}_{i}{ext}")
                    i += 1

            with open(path, "wb") as f:
                f.write(content)
            add_record(self.db, fname, os.path.getsize(path))
            break

        self._empty(204)

    def _empty(self, code):
        self.send_response(code)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass  # silent


# ── Main ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="文件上传服务器")
    parser.add_argument("-p", "--port", type=int, default=8000)
    args = parser.parse_args()

    # auto-detect LAN IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    url = f"http://{ip}:{args.port}"
    Handler.db = init_db()

    server = HTTPServer(("0.0.0.0", args.port), Handler)

    print(f"  ✅ 上传服务已启动")
    print(f"  📱 手机浏览器访问: {url}")
    print(f"  📁 文件目录: {UPLOAD_DIR}")
    print(f"  ⏹️  Ctrl+C 停止\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 已停止")
        server.server_close()
        Handler.db.close()


if __name__ == "__main__":
    main()
