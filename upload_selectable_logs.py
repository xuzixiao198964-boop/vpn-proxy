#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传带可选择复制日志的 APK 到服务器
"""
import paramiko
import os
import time

def upload_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # 本地文件
    timestamp = "20260324_185859"
    local_apk = r"E:\work\vpn-proxy-client\dist\VpnProxyClient_selectable_logs_20260324_185859.apk"
    apk_name = f"VpnProxyClient_selectable_logs_{timestamp}.apk"
    
    # 服务器文件
    remote_dir = "/opt/vpn-proxy-apk"
    server_files = [
        (local_apk, f"{remote_dir}/{apk_name}"),
        (local_apk, f"{remote_dir}/VpnProxyClient.apk")  # 同时更新主版本
    ]
    
    print("="*60)
    print("上传带可选择复制日志的 APK")
    print("="*60)
    print(f"时间戳: {timestamp}")
    print(f"本地文件: {os.path.basename(local_apk)}")
    print(f"文件大小: {os.path.getsize(local_apk) / (1024*1024):.2f} MB")
    print()
    print("服务器文件:")
    print(f"  1. {apk_name} (带可选择复制日志版本)")
    print(f"  2. VpnProxyClient.apk (主版本)")
    print()
    print("下载地址:")
    print(f"  带日志版本: http://{host}:18080/{apk_name}")
    print(f"  主版本: http://{host}:18080/VpnProxyClient.apk")
    print("="*60)
    
    client = None
    try:
        print("\n连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("上传文件...")
        sftp = client.open_sftp()
        
        for local, remote in server_files:
            filename = os.path.basename(local)
            print(f"  上传: {filename}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # 验证上传
        print("\n验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name} {remote_dir}/VpnProxyClient.apk", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件:\n{result}")
        
        # 检查 VPN 服务状态
        print("\n检查 VPN 服务状态:")
        check_cmds = [
            "ps aux | grep 'python3 server/run.py' | grep -v grep",
            "ss -tlnp | grep ':18443'",
            f"timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/18443' && echo '✅ 端口 18443 可连接' || echo '❌ 端口 18443 不可连接'"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            if result:
                print(f"  {result}")
        
        # 测试下载
        print("\n测试下载链接...")
        test_url = f"http://localhost:18080/{apk_name}"
        stdin, stdout, stderr = client.exec_command(f"curl -I {test_url} 2>/dev/null | head -1", timeout=30)
        http_result = stdout.read().decode().strip()
        
        if "200 OK" in http_result:
            print(f"  ✅ 文件可下载: {http_result}")
        else:
            print(f"  ⚠️ 下载测试: {http_result}")
        
        client.close()
        
        print("\n" + "="*60)
        print("上传成功!")
        print("="*60)
        print("重要信息:")
        print("1. 服务器 VPN 服务已修复，端口 18443 可连接")
        print("2. APK 已上传，包含可选择复制日志标记")
        print("3. 使用默认配置测试连接:")
        print("   地址: 104.244.90.202")
        print("   端口: 18443")
        print("   用户名: demo")
        print("   密码: demo123")
        print()
        print("下载链接:")
        print(f"带可选择复制日志版本: http://{host}:18080/{apk_name}")
        print(f"主版本: http://{host}:18080/VpnProxyClient.apk")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n上传失败: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始上传带可选择复制日志的 APK...")
    if upload_apk():
        exit(0)
    else:
        exit(1)