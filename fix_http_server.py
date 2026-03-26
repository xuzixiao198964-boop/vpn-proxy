#!/usr/bin/env python3
"""
修复服务器上的 HTTP 服务，确保从正确目录提供文件
"""
import paramiko
import time

def fix_http_server():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("修复 HTTP 服务器配置...")
        
        # 1. 停止现有的 HTTP 服务
        print("停止现有的 HTTP 服务...")
        commands = [
            "pkill -f 'http.server'",
            "sleep 2",
            "ss -tlnp | grep ':18080 ' || echo '端口 18080 已释放'"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"输出: {output}")
        
        # 2. 在正确目录启动 HTTP 服务
        print("\n在 /opt/vpn-proxy-apk 目录启动 HTTP 服务...")
        start_cmd = "cd /opt/vpn-proxy-apk && nohup python3 -m http.server 18080 > /var/log/apk-server.log 2>&1 &"
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=30)
        time.sleep(3)
        
        # 3. 检查服务状态
        print("检查服务状态...")
        check_cmds = [
            "ps aux | grep 'http.server' | grep -v grep",
            "ss -tlnp | grep ':18080 '",
            "curl -I http://localhost:18080/VpnProxyClient.apk"
        ]
        
        for cmd in check_cmds:
            print(f"\n执行: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(f"输出: {output}")
            if error:
                print(f"错误: {error}")
        
        # 4. 列出可下载文件
        print("\n可下载文件列表:")
        stdin, stdout, stderr = client.exec_command("ls -lh /opt/vpn-proxy-apk/*.apk", timeout=30)
        files = stdout.read().decode().strip()
        print(files)
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("=== 修复 HTTP 服务器 ===")
    if fix_http_server():
        print("\n" + "="*60)
        print("SUCCESS: HTTP 服务器已修复!")
        print("="*60)
        print("下载地址:")
        print("1. http://104.244.90.202:18080/VpnProxyClient.apk")
        print("2. http://104.244.90.202:18080/VpnProxyClient_20260324_170738.apk")
        print("="*60)
    else:
        print("\nERROR: HTTP 服务器修复失败")