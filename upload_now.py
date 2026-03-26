#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立即上传文件到服务器并验证
"""
import paramiko
import os
import sys

def upload_file():
    # 服务器信息
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # 本地文件
    apk_name = "VpnProxyClient_app_logs_20260324_201010.apk"
    local_apk = r"E:\work\vpn-proxy-client\dist\VpnProxyClient_app_logs_20260324_201010.apk"
    
    if not os.path.exists(local_apk):
        print(f"错误: 文件不存在: {local_apk}")
        return False
    
    file_size = os.path.getsize(local_apk)
    file_size_mb = file_size / (1024*1024)
    
    print("开始上传...")
    print(f"服务器: {host}:{port}")
    print(f"用户名: {username}")
    print(f"文件: {apk_name}")
    print(f"大小: {file_size_mb:.2f} MB")
    
    client = None
    try:
        # 连接服务器
        print("连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=15)
        print("连接成功")
        
        # 上传文件
        print("上传文件...")
        sftp = client.open_sftp()
        
        remote_dir = "/opt/vpn-proxy-apk"
        
        # 上传带时间戳版本
        remote_file = f"{remote_dir}/{apk_name}"
        sftp.put(local_apk, remote_file)
        print(f"上传: {apk_name}")
        
        # 同时更新主版本
        remote_main = f"{remote_dir}/VpnProxyClient.apk"
        sftp.put(local_apk, remote_main)
        print("更新: VpnProxyClient.apk")
        
        sftp.close()
        
        # 验证上传
        print("验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name}", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件: {result}")
        
        # 测试下载
        print("测试下载链接...")
        test_cmd = f"curl -I http://localhost:18080/{apk_name} 2>/dev/null | head -1"
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        http_result = stdout.read().decode().strip()
        
        if "200 OK" in http_result:
            print("下载链接可用")
            
            # 获取文件大小
            size_cmd = f"curl -sI http://localhost:18080/{apk_name} 2>/dev/null | grep -i 'content-length:' | cut -d' ' -f2"
            stdin, stdout, stderr = client.exec_command(size_cmd, timeout=30)
            server_size = stdout.read().decode().strip()
            
            if server_size:
                server_size_mb = int(server_size) / (1024*1024)
                print(f"服务器文件大小: {server_size_mb:.2f} MB")
        
        client.close()
        
        print("\n上传成功!")
        print(f"下载地址: http://{host}:18080/{apk_name}")
        return True
        
    except Exception as e:
        print(f"上传失败: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("使用服务器信息:")
    print("IP: 104.244.90.202")
    print("端口: 22")
    print("用户名: root")
    print("密码: v9wSxMxg92dp")
    print()
    
    success = upload_file()
    if success:
        print("\n✅ 上传完成!")
        print("下载地址: http://104.244.90.202:18080/VpnProxyClient_app_logs_20260324_201010.apk")
        sys.exit(0)
    else:
        print("\n❌ 上传失败")
        sys.exit(1)