#!/usr/bin/env python3
"""
简单 HTTP 服务器，在 18080 端口提供 APK 下载
"""
import http.server
import socketserver
import os
import sys

PORT = 18080
APK_PATH = os.path.join(os.path.dirname(__file__), 'dist', 'VpnProxyClient-debug.apk')

class ApkHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/vpnproxy.apk' or self.path == '/':
            if os.path.exists(APK_PATH):
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.android.package-archive')
                self.send_header('Content-Disposition', 'attachment; filename="VpnProxyClient.apk"')
                self.send_header('Content-Length', str(os.path.getsize(APK_PATH)))
                self.end_headers()
                
                with open(APK_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'APK not found')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
            <head><title>VPN Proxy Client APK</title></head>
            <body>
                <h1>VPN Proxy Client APK 下载</h1>
                <p>文件大小: {os.path.getsize(APK_PATH) // 1024 // 1024} MB</p>
                <p><a href="/vpnproxy.apk">点击下载 APK</a></p>
                <p>下载地址: http://[服务器IP]:{PORT}/vpnproxy.apk</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

def main():
    if not os.path.exists(APK_PATH):
        print(f"错误: APK 文件不存在: {APK_PATH}")
        sys.exit(1)
    
    print(f"APK 文件: {APK_PATH}")
    print(f"文件大小: {os.path.getsize(APK_PATH) // 1024 // 1024} MB")
    print(f"启动 HTTP 服务器在端口 {PORT}...")
    print(f"下载地址: http://0.0.0.0:{PORT}/vpnproxy.apk")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), ApkHandler) as httpd:
        print(f"服务器已启动，按 Ctrl+C 停止")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    main()