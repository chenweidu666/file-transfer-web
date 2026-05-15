#!/usr/bin/env python3
import os
import html
from http.server import HTTPServer, SimpleHTTPRequestHandler
import argparse

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

HTML = '''<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>文件上传</title>
<style>
  body { max-width: 500px; margin: 40px auto; padding: 20px; font-family: system-ui; }
  h2 { text-align: center; }
  form { display: flex; flex-direction: column; gap: 12px; }
  input[type="file"] { padding: 10px; border: 2px dashed #ccc; border-radius: 8px; background: #fafafa; }
  button { padding: 14px; background: #4f46e5; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
  button:hover { background: #4338ca; }
  .msg { text-align: center; padding: 10px; border-radius: 6px; }
  .ok { background: #dcfce7; color: #166534; }
  .err { background: #fee2e2; color: #991b1b; }
  .files { margin-top: 20px; }
  .files a { display: block; padding: 8px; color: #4f46e5; text-decoration: none; border-bottom: 1px solid #eee; }
</style></head>
<body>
<h2>&#128228; 文件上传</h2>
<form method="post" enctype="multipart/form-data" action="/upload">
  <input type="file" name="file" multiple>
  <button type="submit">上传</button>
</form>
<div class="files"><b>已上传的文件 (在 {UPLOAD_DIR} 目录):</b>
{FILE_LIST}</div>
</body></html>
'''

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/upload':
            self.send_html()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            length = int(self.headers.get('Content-Length', 0))
            boundary = self.headers.get('Content-Type','').split('boundary=')[-1].encode()
            data = self.rfile.read(length)
            self._parse_and_save(data, boundary)
        else:
            self.send_error(404)

    def send_html(self):
        files = sorted(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else []
        flist = '\n'.join(f'<a href="/uploads/{html.escape(f)}">{html.escape(f)} ({os.path.getsize(os.path.join(UPLOAD_DIR,f))} B)</a>' for f in files)
        body = HTML.replace('{UPLOAD_DIR}', html.escape(UPLOAD_DIR)).replace('{FILE_LIST}', flist if files else '<p style="color:#999">暂无</p>')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode())

    def _parse_and_save(self, data, boundary):
        parts = data.split(b'--' + boundary)
        for part in parts:
            if b'filename=' in part:
                header, _, rest = part.partition(b'\r\n\r\n')
                name = header.decode().split('filename="')[1].split('"')[0]
                content = rest.rstrip(b'\r\n').rstrip(b'--\r\n')
                if name and content:
                    path = os.path.join(UPLOAD_DIR, name)
                    # add suffix if exists
                    if os.path.exists(path):
                        base, ext = os.path.splitext(name)
                        i = 1
                        while os.path.exists(path):
                            path = os.path.join(UPLOAD_DIR, f'{base}_{i}{ext}')
                            i += 1
                    with open(path, 'wb') as f:
                        f.write(content)
                    self.send_response(302)
                    self.send_header('Location', '/?ok=1')
                    self.end_headers()
                    return
        self.send_response(302)
        self.send_header('Location', '/?err=1')
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f'[{self.log_date_time_string()}] {fmt % args}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000)
    args = parser.parse_args()
    server = HTTPServer(('0.0.0.0', args.port), Handler)
    print(f'\n  上传服务已启动！')
    print(f'  请在手机浏览器中打开: http://192.168.31.119:{args.port}\n')
    print(f'  上传的文件保存在: {UPLOAD_DIR}\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务已停止')
        server.server_close()
