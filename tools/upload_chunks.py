#!/usr/bin/env python3
import paramiko
import os
import math

def upload_large_file():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    local_path = "E:\\work\\vpn-proxy-client\\dist\\VpnProxyClient-debug.apk"
    remote_dir = "/opt/downloads"
    remote_filename = "VpnProxyClient-debug.apk"
    remote_path = f"{remote_dir}/{remote_filename}"
    
    # 读取文件
    with open(local_path, 'rb') as f:
        file_data = f.read()
    
    file_size = len(file_data)
    print(f"文件大小: {file_size} 字节")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"连接到 {host}...")
        ssh.connect(host, port, username, password, timeout=30)
        print("连接成功")
        
        # 使用 SFTP 上传
        sftp = ssh.open_sftp()
        
        # 删除可能存在的旧文件
        try:
            sftp.remove(remote_path)
            print("删除旧文件")
        except:
            pass
        
        # 分块上传（每块 5MB）
        chunk_size = 5 * 1024 * 1024  # 5MB
        with sftp.open(remote_path, 'wb') as remote_file:
            uploaded = 0
            
            for i in range(0, file_size, chunk_size):
                chunk = file_data[i:i+chunk_size]
                remote_file.write(chunk)
                uploaded += len(chunk)
                
                # 显示进度
                percent = (uploaded / file_size) * 100
                print(f"上传进度: {uploaded}/{file_size} 字节 ({percent:.1f}%)")
        
        sftp.close()
        print("上传完成")
        
        # 验证文件
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {remote_path}")
        print("服务器上的文件:", stdout.read().decode().strip())
        
        # 测试下载
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -I http://localhost:11000/{remote_filename} | grep -i content-length")
        print("HTTP 服务器测试:", stdout.read().decode().strip())
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    upload_large_file()