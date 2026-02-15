#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir('/root/.openclaw/workspace/web/chat')
PORT = 8090

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"HTTP服务器启动在端口 {PORT}")
    httpd.serve_forever()
