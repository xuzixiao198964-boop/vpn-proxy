#!/usr/bin/env python3
import paramiko
import os
from scp import SCPClient

def upload_file():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    local_path = "E:\\work\\vpn-proxy-client\\dist\\VpnProxyClient-debug.apk"
    remote_path = "/var/www/html/VpnProxyClient-debug.apk"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        ssh.connect(host, port, username, password, timeout=30)
        print("Connected successfully")
        
        # Upload file
        with SCPClient(ssh.get_transport()) as scp:
            print(f"Uploading {local_path} to {remote_path}...")
            scp.put(local_path, remote_path)
            print("Upload completed successfully")
        
        # Verify file
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {remote_path}")
        print("File on server:", stdout.read().decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    upload_file()