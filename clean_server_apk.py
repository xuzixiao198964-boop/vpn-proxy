#!/usr/bin/env python3
"""
清理服务器上的 APK 文件
"""
import paramiko
import os

def clean_server_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("清理服务器上的 APK 文件...")
        
        # 清理 /opt/vpn-proxy-apk 目录
        commands = [
            "ls -la /opt/vpn-proxy-apk/",
            "rm -f /opt/vpn-proxy-apk/*.apk",
            "rm -f /opt/vpn-proxy-apk/*.APK",
            "ls -la /opt/vpn-proxy-apk/"
        ]
        
        for cmd in commands:
            print(f"\n执行: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(f"输出: {output}")
            if error:
                print(f"错误: {error}")
        
        print("\nSUCCESS: 服务器 APK 文件已清理")
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    clean_server_apk()