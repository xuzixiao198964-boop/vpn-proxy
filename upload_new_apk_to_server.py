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
    base_dir = "E:/work/vpn-proxy-client/downloaded_apk"
    local_main_apk = os.path.join(base_dir, "VpnProxyClient.apk")
    local_timestamp_apk = os.path.join(base_dir, "VpnProxyClient_20260324_180449.apk")
    
    remote_dir = "/opt/vpn-proxy-apk"
    remote_main_apk = f"{remote_dir}/VpnProxyClient.apk"
    remote_timestamp_apk = f"{remote_dir}/VpnProxyClient_20260324_180449.apk"
    
    # 检查文件
    files_to_upload = [
        (local_main_apk, remote_main_apk),
        (local_timestamp_apk, remote_timestamp_apk)
    ]
    
    for local, remote in files_to_upload:
        if not os.path.exists(local):
            print(f"错误: 文件不存在: {local}")
            return False
    
    client = None
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 上传 APK 到服务器 ===")
        
        # 确保目录存在
        print(f"确保目录存在: {remote_dir}")
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}", timeout=30)
        
        # 使用 SFTP 上传文件
        print("上传文件...")
        sftp = client.open_sftp()
        
        for local, remote in files_to_upload:
            print(f"  上传: {os.path.basename(local)} -> {remote}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # 验证上传
        print("\n验证上传的文件:")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/*.apk", timeout=30)
        result = stdout.read().decode().strip()
        print(result)
        
        # 检查 HTTP 服务
        print("\n检查 HTTP 服务状态:")
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18080 '", timeout=30)
        port_check = stdout.read().decode().strip()
        print(f"18080 端口: {port_check}")
        
        # 测试下载
        print("\n测试下载链接...")
        test_cmds = [
            f"curl -I http://localhost:18080/VpnProxyClient.apk",
            f"curl -I http://localhost:18080/VpnProxyClient_20260324_180449.apk"
        ]
        
        for cmd in test_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            if "200 OK" in result:
                print(f"  ✅ {cmd.split()[-1]}: 可访问")
            else:
                print(f"  ❌ {cmd.split()[-1]}: {result.split()[0] if result else '未知错误'}")
        
        print("\n" + "="*60)
        print("SUCCESS: APK 上传完成!")
        print("="*60)
        print("下载地址:")
        print(f"1. 主版本: http://{host}:18080/VpnProxyClient.apk")
        print(f"2. 带时间戳: http://{host}:18080/VpnProxyClient_20260324_180449.apk")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"上传错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始上传 APK 到服务器...")
    if upload_apk():
        sys.exit(0)
    else:
        sys.exit(1)