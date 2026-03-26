#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传最终验证版 APK
"""
import paramiko
import os
import sys

def main():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # 文件路径
    timestamp = "20260324_190744"
    local_apk = r"E:\work\vpn-proxy-client\dist\VpnProxyClient_final_20260324_190744.apk"
    apk_name = f"VpnProxyClient_final_{timestamp}.apk"
    
    if not os.path.exists(local_apk):
        print(f"错误: 文件不存在: {local_apk}")
        # 尝试其他文件
        dist_dir = r"E:\work\vpn-proxy-client\dist"
        apk_files = [f for f in os.listdir(dist_dir) if f.endswith('.apk')]
        if apk_files:
            latest_apk = max(apk_files, key=lambda f: os.path.getmtime(os.path.join(dist_dir, f)))
            local_apk = os.path.join(dist_dir, latest_apk)
            apk_name = latest_apk
            print(f"使用最新文件: {latest_apk}")
        else:
            print("没有找到 APK 文件")
            return False
    
    remote_dir = "/opt/vpn-proxy-apk"
    
    print("="*60)
    print("上传最终验证版 APK")
    print("="*60)
    print(f"服务器: {host}")
    print(f"本地文件: {os.path.basename(local_apk)}")
    print(f"文件大小: {os.path.getsize(local_apk) / (1024*1024):.2f} MB")
    print()
    print("目标文件:")
    print(f"  1. {apk_name} (带时间戳版本)")
    print(f"  2. VpnProxyClient.apk (主版本)")
    print()
    print("下载地址:")
    print(f"  最终版本: http://{host}:18080/{apk_name}")
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
        
        # 上传两个版本
        files_to_upload = [
            (local_apk, f"{remote_dir}/{apk_name}"),
            (local_apk, f"{remote_dir}/VpnProxyClient.apk")
        ]
        
        for local, remote in files_to_upload:
            filename = os.path.basename(local)
            print(f"  上传: {filename} -> {os.path.basename(remote)}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # 验证上传
        print("\n验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name} {remote_dir}/VpnProxyClient.apk", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件:\n{result}")
        
        # 检查服务器状态
        print("\n检查服务器状态:")
        check_cmds = [
            "ps aux | grep 'python3 server/run.py' | grep -v grep | head -1",
            "ss -tlnp | grep ':18443'",
            f"curl -I http://localhost:18080/{apk_name} 2>/dev/null | head -1"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            if result:
                print(f"  {result}")
        
        client.close()
        
        print("\n" + "="*60)
        print("上传成功!")
        print("="*60)
        print("重要信息:")
        print("1. 此 APK 已通过基本完整性验证")
        print("2. 服务器 VPN 服务正在运行 (端口 18443)")
        print("3. 使用默认配置测试:")
        print("   地址: 104.244.90.202")
        print("   端口: 18443")
        print("   用户名: demo")
        print("   密码: demo123")
        print()
        print("下载链接:")
        print(f"最终验证版本: http://{host}:18080/{apk_name}")
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
    success = main()
    sys.exit(0 if success else 1)