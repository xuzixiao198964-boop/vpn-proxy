#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务器上的损坏 APK 文件
"""
import paramiko
import os
import time

def fix_server_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    print("="*60)
    print("修复服务器上的损坏 APK 文件")
    print("="*60)
    
    # 本地完整的 APK
    local_good_apk = r"E:\work\vpn-proxy-client\downloaded_apk\VpnProxyClient.apk"
    if not os.path.exists(local_good_apk):
        print(f"错误: 本地完整 APK 不存在: {local_good_apk}")
        return False
    
    file_size = os.path.getsize(local_good_apk)
    print(f"本地完整 APK: {os.path.basename(local_good_apk)}")
    print(f"文件大小: {file_size / (1024*1024):.2f} MB")
    print(f"应该是: ~64 MB (如果只有 10MB 就是损坏的)")
    
    client = None
    try:
        print("\n连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        # 1. 检查服务器上的 APK
        print("\n1. 检查服务器上的 APK 文件:")
        remote_dir = "/opt/vpn-proxy-apk"
        check_cmds = [
            f"ls -lh {remote_dir}/VpnProxyClient.apk",
            f"du -h {remote_dir}/VpnProxyClient.apk",
            f"file {remote_dir}/VpnProxyClient.apk 2>/dev/null || echo 'file命令不可用'"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            print(f"  {cmd}: {result}")
            
            # 检查文件大小
            if "10." in result and "M" in result:
                print("  ⚠️  发现损坏的 APK (只有 ~10MB)")
        
        # 2. 上传完整的 APK
        print("\n2. 上传完整的 APK 到服务器...")
        sftp = client.open_sftp()
        
        # 上传主版本
        remote_main = f"{remote_dir}/VpnProxyClient.apk"
        print(f"  上传: {os.path.basename(local_good_apk)} -> VpnProxyClient.apk")
        sftp.put(local_good_apk, remote_main)
        
        # 上传带时间戳版本
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        remote_timestamp = f"{remote_dir}/VpnProxyClient_fixed_{timestamp}.apk"
        print(f"  上传: {os.path.basename(local_good_apk)} -> VpnProxyClient_fixed_{timestamp}.apk")
        sftp.put(local_good_apk, remote_timestamp)
        
        sftp.close()
        
        # 3. 验证上传
        print("\n3. 验证上传的文件:")
        verify_cmds = [
            f"ls -lh {remote_dir}/VpnProxyClient.apk {remote_dir}/VpnProxyClient_fixed_{timestamp}.apk",
            f"echo '文件数量:' && ls {remote_dir}/*.apk | wc -l"
        ]
        
        for cmd in verify_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            print(f"  {result}")
        
        # 4. 测试下载
        print("\n4. 测试下载链接:")
        test_urls = [
            f"http://localhost:18080/VpnProxyClient.apk",
            f"http://localhost:18080/VpnProxyClient_fixed_{timestamp}.apk"
        ]
        
        for url in test_urls:
            cmd = f"curl -I {url} 2>/dev/null | head -1"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            http_result = stdout.read().decode().strip()
            
            cmd_size = f"curl -sI {url} 2>/dev/null | grep -i 'content-length:' | cut -d' ' -f2"
            stdin, stdout, stderr = client.exec_command(cmd_size, timeout=30)
            size_result = stdout.read().decode().strip()
            
            if size_result:
                size_mb = int(size_result) / (1024*1024)
                print(f"  {url}: {http_result}, 大小: {size_mb:.2f} MB")
                
                if size_mb > 60:
                    print(f"    ✅ 文件大小正常 (~64 MB)")
                else:
                    print(f"    ❌ 文件大小异常: {size_mb:.2f} MB")
            else:
                print(f"  {url}: {http_result}")
        
        # 5. 检查 HTTP 服务
        print("\n5. 检查 HTTP 服务:")
        stdin, stdout, stderr = client.exec_command("ps aux | grep 'python3.*18080' | grep -v grep", timeout=30)
        http_process = stdout.read().decode().strip()
        if http_process:
            print(f"  HTTP 服务运行中: {http_process}")
        else:
            print("  ⚠️  HTTP 服务可能未运行")
            # 重启 HTTP 服务
            restart_cmd = "cd /opt/vpn-proxy-apk && python3 -m http.server 18080 > /dev/null 2>&1 &"
            stdin, stdout, stderr = client.exec_command(restart_cmd, timeout=30)
            print("  已尝试重启 HTTP 服务")
        
        client.close()
        
        print("\n" + "="*60)
        print("修复完成!")
        print("="*60)
        print("问题原因: 服务器上的 APK 文件损坏（只有 ~10MB）")
        print("修复措施: 已上传完整的 APK 文件（~64 MB）")
        print()
        print("下载地址:")
        print(f"1. 主版本: http://{host}:18080/VpnProxyClient.apk")
        print(f"2. 修复版本: http://{host}:18080/VpnProxyClient_fixed_{timestamp}.apk")
        print()
        print("测试说明:")
        print("1. 重新下载 APK（现在应该是完整的 64MB）")
        print("2. 安装测试（应该不会再'解析包出问题'）")
        print("3. 使用默认配置连接 VPN")
        print("="*60)
        
        return True, timestamp
        
    except Exception as e:
        print(f"\n修复失败: {e}")
        return False, None
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始修复服务器 APK 文件...")
    success, timestamp = fix_server_apk()
    exit(0 if success else 1)