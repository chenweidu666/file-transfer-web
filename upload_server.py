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


class FileUploadServer:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.upload_dir = os.path.join(self.data_dir, "uploads")
        self.db_path = os.path.join(self.data_dir, "upload.db")
        
        # Create directories
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize database
        self.init_db()

    def init_db(self):
        """Initialize SQLite database for upload records."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_upload_record(self, filename, size):
        """Add a record of uploaded file to the database."""
        conn = sqlite3.connect(self.db_path)
        record_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute(
            "INSERT INTO uploads (id, name, size, uploaded_at) VALUES (?, ?, ?, ?)",
            (record_id, filename, size, timestamp)
        )
        conn.commit()
        conn.close()
        return record_id

    def get_upload_records(self):
        """Get all upload records from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT id, name, size, uploaded_at FROM uploads ORDER BY uploaded_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {"id": row[0], "name": row[1], "size": row[2], "uploaded_at": row[3]}
            for row in rows
        ]

    def delete_upload_record(self, record_id):
        """Delete a specific upload record and associated file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM uploads WHERE id = ?", (record_id,)
        )
        result = cursor.fetchone()
        
        if result:
            filename = result[0]
            filepath = os.path.join(self.upload_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            conn.execute("DELETE FROM uploads WHERE id = ?", (record_id,))
            conn.commit()
        
        conn.close()

    def clear_all_records(self):
        """Clear all upload records and associated files."""
        records = self.get_upload_records()
        conn = sqlite3.connect(self.db_path)
        
        for record in records:
            filepath = os.path.join(self.upload_dir, record["name"])
            if os.path.exists(filepath):
                os.remove(filepath)
        
        conn.execute("DELETE FROM uploads")
        conn.commit()
        conn.close()


HTML_TEMPLATE = """<!DOCTYPE html>
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
drop.ondrop=e=>{e.preventDefault();drop.classList.remove('over');file.files=e.dataTransfer.files;updateFileCount()};
file.onchange=updateFileCount;

function updateFileCount(){
    const n=file.files.length;
    btn.disabled=!n;
    btn.textContent=n?`上传 ${n} 个文件`:'上传选中文件';
}

form.onsubmit=e=>{
    e.preventDefault();
    if(!file.files.length)return;
    
    bar.style.display='block';
    btn.disabled=true;
    btn.textContent='上传中...';
    fill.style.width='0%';
    
    const fd=new FormData();
    for(const f of file.files) fd.append('file',f,f.name);
    
    const xhr=new XMLHttpRequest();
    xhr.open('POST','/upload');
    xhr.upload.onprogress=ev=>{
        if(ev.lengthComputable){
            const p=Math.round(ev.loaded/ev.total*100);
            fill.style.width=p+'%';
            btext.textContent=p+'%';
        }
    };
    xhr.onload=()=>{
        if(xhr.status===204){
            bar.style.display='none';
            file.value='';
            updateFileCount();
            loadHistory();
        } else {
            alert('上传失败: ' + xhr.status);
            bar.style.display='none';
            btn.disabled=false;
            btn.textContent='上传选中文件';
        }
    };
    xhr.onerror=()=>{
        alert('上传错误');
        bar.style.display='none';
        btn.disabled=false;
        btn.textContent='上传选中文件';
    };
    xhr.send(fd);
};

clearBtn.onclick=()=>{
    if(confirm('确定清空所有记录？')){
        fetch('/api/clear', {method:'POST'})
            .then(() => loadHistory())
            .catch(err => console.error('Clear error:', err));
    }
};

function formatSize(bytes){
    const units=['B','KB','MB','GB'];
    let size=bytes;
    let i=0;
    while(size>=1024&&i<units.length-1){
        size/=1024;
        i++;
    }
    return (Math.round(size*10)/10) + ' ' + units[i];
}

function loadHistory(){
    fetch('/api/history')
        .then(response => response.json())
        .then(rows => {
            if(!rows.length){
                list.innerHTML='<div class="empty">暂无记录</div>';
                return;
            }
            list.innerHTML=rows.map(r=>{
                const encodedName=encodeURIComponent(r.name);
                return `
                <div class="row" id="r-${r.id}">
                    <div class="info">
                        <div class="fname" title="${r.name}">${r.name}</div>
                        <meta>${r.uploaded_at} · ${formatSize(r.size)}</meta>
                    </div>
                    <a class="dl" href="/uploads/${encodedName}">下载</a>
                    <button class="del" onclick="deleteRecord('${r.id}')">✕</button>
                </div>`;
            }).join('');
        })
        .catch(err => console.error('Load history error:', err));
}

function deleteRecord(id){
    fetch('/api/delete', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({id:id})
    })
    .then(() => loadHistory())
    .catch(err => console.error('Delete error:', err));
}

// Load history on page load
document.addEventListener('DOMContentLoaded', loadHistory);
</script>
</body>
</html>
"""


class RequestHandler(SimpleHTTPRequestHandler):
    server_instance = None  # Will be set to the FileUploadServer instance
    
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.serve_page()
        elif self.path.startswith("/uploads/"):
            # Serve uploaded files
            filename = self.path[len("/uploads/"):]
            filepath = os.path.join(self.server_instance.upload_dir, filename)
            
            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.serve_file(filepath)
            else:
                self.send_error(404)
        elif self.path == "/api/history":
            self.serve_history()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/upload":
            self.handle_upload()
        elif self.path == "/api/delete":
            self.handle_delete()
        elif self.path == "/api/clear":
            self.handle_clear()
        else:
            self.send_error(404)

    def serve_page(self):
        """Serve the main upload page."""
        body = HTML_TEMPLATE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filepath):
        """Serve an uploaded file."""
        try:
            with open(filepath, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(os.path.getsize(filepath)))
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")

    def serve_history(self):
        """Serve the upload history as JSON."""
        try:
            records = self.server_instance.get_upload_records()
            data = json.dumps(records).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, f"Error getting history: {str(e)}")

    def handle_upload(self):
        """Handle file upload POST request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_error(400, "No content")
                return

            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_error(400, "Invalid content type")
                return

            # Parse multipart data manually
            boundary = content_type.split("boundary=")[-1].encode()
            raw_data = self.rfile.read(content_length)
            parts = raw_data.split(b"--" + boundary)

            uploaded_any = False
            
            for part in parts:
                # Find the header section
                header_end_idx = part.find(b"\r\n\r\n")
                if header_end_idx == -1:
                    continue
                
                header_section = part[:header_end_idx].decode("utf-8", errors="ignore")
                
                # Check if this part contains a file
                if 'filename="' not in header_section:
                    continue
                
                # Extract filename
                filename_start = header_section.find('filename="') + len('filename="')
                filename_end = header_section.find('"', filename_start)
                if filename_start == -1 or filename_end == -1:
                    continue
                
                filename = header_section[filename_start:filename_end]
                if not filename:
                    continue
                
                # Extract file content
                content = part[header_end_idx + 4:]
                # Remove trailing boundary if present
                if content.endswith(b"\r\n"):
                    content = content[:-2]
                
                if not content:
                    continue
                
                # Save file
                filepath = os.path.join(self.server_instance.upload_dir, filename)
                
                # Handle duplicate filenames
                if os.path.exists(filepath):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(filepath):
                        new_filename = f"{base}_{counter}{ext}"
                        filepath = os.path.join(self.server_instance.upload_dir, new_filename)
                        counter += 1
                    filename = new_filename
                
                with open(filepath, "wb") as f:
                    f.write(content)
                
                # Add record to database
                self.server_instance.add_upload_record(filename, len(content))
                uploaded_any = True

            if uploaded_any:
                self.send_response(204)  # Success, no content
            else:
                self.send_error(400, "No valid files found in upload")
            
            self.end_headers()
            
        except Exception as e:
            print(f"Upload error: {str(e)}")
            self.send_error(500, f"Upload error: {str(e)}")

    def handle_delete(self):
        """Handle record deletion."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            
            record_id = data.get("id")
            if not record_id:
                self.send_error(400, "Missing record id")
                return
            
            self.server_instance.delete_upload_record(record_id)
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            print(f"Delete error: {str(e)}")
            self.send_error(500, f"Delete error: {str(e)}")

    def handle_clear(self):
        """Handle clearing all records."""
        try:
            self.server_instance.clear_all_records()
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            print(f"Clear error: {str(e)}")
            self.send_error(500, f"Clear error: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="文件上传服务器")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to run server on")
    args = parser.parse_args()

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_instance = FileUploadServer(script_dir)

    # Auto-detect local IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    # Set the server instance for the handler
    RequestHandler.server_instance = server_instance

    server_address = ("0.0.0.0", args.port)
    httpd = HTTPServer(server_address, RequestHandler)

    print(f"\n  ✅ 上传服务已启动")
    print(f"  📱 手机浏览器访问: http://{ip}:{args.port}")
    print(f"  📁 上传文件目录: {server_instance.upload_dir}")
    print(f"  🗂️  数据库位置: {server_instance.db_path}")
    print(f"  ⏹️  按 Ctrl+C 停止服务\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        httpd.server_close()


if __name__ == "__main__":
    main()