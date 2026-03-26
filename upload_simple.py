#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单上传脚本
"""
import paramiko
import os

def main():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # 本地文件
    local_apk = r"E:\work\vpn-proxy-client\downloaded_apk\VpnProxyClient_with_logs_20260324_182446.apk"
    timestamp = "20260324_182446"
    
    # 服务器文件
    remote_dir = "/opt/vpn-proxy-apk"
    server_files = [
        (local_apk, f"{remote_dir}/VpnProxyClient.apk"),
        (local_apk, f"{remote_dir}/VpnProxyClient_with_logs_{timestamp}.apk")
    ]
    
    try:
        print("Connecting to server...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("Uploading files...")
        sftp = client.open_sftp()
        
        for local, remote in server_files:
            filename = os.path.basename(local)
            print(f"  Uploading: {filename}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # Verify
        print("Verifying upload...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/VpnProxyClient*.apk")
        result = stdout.read().decode().strip()
        print(f"Server files:\n{result}")
        
        client.close()
        print("Upload successful!")
        
        print("\n" + "="*60)
        print("DOWNLOAD LINKS:")
        print("="*60)
        print(f"1. Main version: http://{host}:18080/VpnProxyClient.apk")
        print(f"2. With logs version: http://{host}:18080/VpnProxyClient_with_logs_{timestamp}.apk")
        print("="*60)
        
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    main()