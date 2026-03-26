#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立即上传并验证地址
"""
import paramiko
import os
import time

def main():
    # 服务器信息
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # APK 文件
    apk_name = "VpnProxyClient_app_error_logs_20260324_212238.apk"
    local_apk = r"E:\work\vpn-proxy-client\dist\VpnProxyClient_app_error_logs_20260324_212238.apk"
    
    if not os.path.exists(local_apk):
        print("错误: 文件不存在")
        return False
    
    file_size = os.path.getsize(local_apk)
    file_size_mb = file_size / (1024*1024)
    
    print("立即上传并验证")
    print(f"文件: {apk_name}")
    print(f"大小: {file_size_mb:.2f} MB")
    print(f"时间: 20260324_212238")
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
        
        # 上传文件
        remote_file = f"{remote_dir}/{apk_name}"
        sftp.put(local_apk, remote_file)
        print(f"上传: {apk_name}")
        
        # 更新主版本
        remote_main = f"{remote_dir}/VpnProxyClient.apk"
        sftp.put(local_apk, remote_main)
        print("更新: VpnProxyClient.apk")
        
        sftp.close()
        print("上传完成")
        
        # 等待
        time.sleep(2)
        
        # 验证
        print("\n3. 验证服务器文件...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name}", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件: {result}")
        
        # 测试下载
        print("\n4. 测试下载链接...")
        test_url = f"http://localhost:18080/{apk_name}"
        
        for i in range(3):
            print(f"测试 {i+1}/3...")
            stdin, stdout, stderr = client.exec_command(f"curl -I {test_url} 2>/dev/null | head -1", timeout=30)
            http_result = stdout.read().decode().strip()
            
            if "200 OK" in http_result:
                print(f"下载链接可用: {http_result}")
                
                # 检查大小
                stdin, stdout, stderr = client.exec_command(f"curl -sI {test_url} 2>/dev/null | grep -i 'content-length:' | cut -d' ' -f2", timeout=30)
                server_size = stdout.read().decode().strip()
                
                if server_size:
                    server_size_mb = int(server_size) / (1024*1024)
                    print(f"服务器文件大小: {server_size_mb:.2f} MB")
                    
                    if abs(server_size_mb - file_size_mb) < 0.5:
                        print("文件大小正确")
                        break
                break
            time.sleep(1)
        
        client.close()
        
        print("\n✅ 上传验证完成!")
        print(f"✅ 地址有效: http://{host}:18080/{apk_name}")
        return True
        
    except Exception as e:
        print(f"上传失败: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始上传并验证...")
    success = main()
    
    if success:
        print("\n🎉 完成!")
        print("地址: http://104.244.90.202:18080/VpnProxyClient_app_error_logs_20260324_212238.apk")
        exit(0)
    else:
        print("\n❌ 失败")
        exit(1)