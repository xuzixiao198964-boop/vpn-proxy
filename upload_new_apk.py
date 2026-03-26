#!/usr/bin/env python3
"""
上传新的 APK 到服务器
"""
import paramiko
import os
import sys

def upload_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # APK 文件路径
    local_apk = os.path.join(os.path.dirname(__file__), "dist", "VpnProxyClient.apk")
    timestamped_apk = os.path.join(os.path.dirname(__file__), "dist", "VpnProxyClient_20260324_170738.apk")
    
    remote_dir = "/opt/vpn-proxy-apk"
    remote_apk = f"{remote_dir}/VpnProxyClient.apk"
    
    # 检查文件
    if not os.path.exists(local_apk):
        print(f"错误: APK 文件不存在: {local_apk}")
        return False
    
    if not os.path.exists(timestamped_apk):
        print(f"错误: 带时间戳的 APK 文件不存在: {timestamped_apk}")
        return False
    
    apk_size = os.path.getsize(local_apk) // 1024 // 1024
    print(f"APK 文件: {local_apk}")
    print(f"带时间戳文件: {timestamped_apk}")
    print(f"文件大小: {apk_size} MB")
    
    client = None
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        # 确保目录存在
        print(f"确保远程目录存在: {remote_dir}")
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}", timeout=30)
        
        # 使用 SFTP 上传文件
        print(f"上传 APK 到服务器...")
        sftp = client.open_sftp()
        
        # 上传主文件
        sftp.put(local_apk, remote_apk)
        
        # 也上传带时间戳的版本
        remote_timestamped = f"{remote_dir}/VpnProxyClient_20260324_170738.apk"
        sftp.put(timestamped_apk, remote_timestamped)
        
        sftp.close()
        
        # 验证上传
        print(f"\n验证上传的文件:")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/*.apk", timeout=30)
        result = stdout.read().decode().strip()
        
        if result:
            print(result)
            
            # 检查 HTTP 服务状态
            print(f"\n检查 18080 端口服务状态:")
            stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18080 '", timeout=30)
            port_check = stdout.read().decode().strip()
            
            if port_check:
                print(f"18080 端口运行中: {port_check}")
                print("\n" + "="*50)
                print("SUCCESS: APK 上传完成!")
                print("="*50)
                print(f"下载地址: http://{host}:18080/VpnProxyClient.apk")
                print(f"带时间戳版本: http://{host}:18080/VpnProxyClient_20260324_170738.apk")
                print("="*50)
                
                # 测试下载链接
                print(f"\n测试下载链接...")
                stdin, stdout, stderr = client.exec_command(f"curl -I http://localhost:18080/VpnProxyClient.apk", timeout=30)
                curl_result = stdout.read().decode().strip()
                if "200 OK" in curl_result:
                    print("下载链接测试: OK")
                else:
                    print(f"下载链接测试: {curl_result}")
                    
                return True
            else:
                print("WARNING: 18080 端口未运行")
                return False
        else:
            print("ERROR: 文件上传验证失败")
            return False
            
    except Exception as e:
        print(f"上传错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("=== 上传新的 APK 到服务器 ===")
    if upload_apk():
        sys.exit(0)
    else:
        sys.exit(1)