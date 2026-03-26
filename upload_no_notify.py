#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传不带通知栏日志的 APK
"""
import paramiko
import os
import time

def main():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # APK 文件
    timestamp = "20260324_210629"
    apk_name = f"VpnProxyClient_no_notify_logs_{timestamp}.apk"
    local_apk = rf"E:\work\vpn-proxy-client\dist\{apk_name}"
    
    if not os.path.exists(local_apk):
        print(f"错误: 文件不存在: {local_apk}")
        return False
    
    file_size = os.path.getsize(local_apk)
    file_size_mb = file_size / (1024*1024)
    
    print("上传不带通知栏日志的 APK")
    print(f"文件: {apk_name}")
    print(f"大小: {file_size_mb:.2f} MB")
    print(f"时间: {timestamp}")
    print()
    
    client = None
    try:
        # 连接服务器
        print("1. 连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=15)
        print("连接成功")
        
        # 上传文件
        print("\n2. 上传文件...")
        sftp = client.open_sftp()
        
        remote_dir = "/opt/vpn-proxy-apk"
        
        # 上传带时间戳版本
        remote_file = f"{remote_dir}/{apk_name}"
        print(f"上传: {apk_name}")
        sftp.put(local_apk, remote_file)
        
        # 同时更新主版本
        remote_main = f"{remote_dir}/VpnProxyClient.apk"
        print("更新: VpnProxyClient.apk")
        sftp.put(local_apk, remote_main)
        
        sftp.close()
        print("上传完成")
        
        # 等待文件同步
        time.sleep(3)
        
        # 验证上传
        print("\n3. 验证服务器文件...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name}", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件: {result}")
        
        # 测试下载链接
        print("\n4. 测试下载链接...")
        test_url = f"http://localhost:18080/{apk_name}"
        
        # 多次测试确保稳定
        for i in range(3):
            print(f"测试 {i+1}/3...")
            stdin, stdout, stderr = client.exec_command(f"curl -I {test_url} 2>/dev/null | head -1", timeout=30)
            http_result = stdout.read().decode().strip()
            
            if "200 OK" in http_result:
                print(f"下载链接可用: {http_result}")
                
                # 获取文件大小
                stdin, stdout, stderr = client.exec_command(f"curl -sI {test_url} 2>/dev/null | grep -i 'content-length:' | cut -d' ' -f2", timeout=30)
                server_size = stdout.read().decode().strip()
                
                if server_size:
                    server_size_mb = int(server_size) / (1024*1024)
                    print(f"服务器文件大小: {server_size_mb:.2f} MB")
                    
                    if abs(server_size_mb - file_size_mb) < 0.5:
                        print("文件大小匹配")
                        break
                break
            else:
                print(f"测试失败: {http_result}")
                time.sleep(1)
        
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
    success = main()
    
    if success:
        print("\n✅ 上传完成!")
        print("地址: http://104.244.90.202:18080/VpnProxyClient_no_notify_logs_20260324_210629.apk")
        exit(0)
    else:
        print("\n❌ 上传失败")
        exit(1)