#!/usr/bin/env python3
"""
APK 部署脚本 - 在服务器上运行，提供 APK 下载服务
"""
import os
import sys
import subprocess
import time

def check_server_apk():
    """检查服务器上是否已有 APK 服务运行"""
    try:
        # 检查 18080 端口是否被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 18080))
        sock.close()
        return result == 0
    except:
        return False

def deploy_to_server():
    """部署 APK 服务到服务器"""
    print("=== APK 部署脚本 ===")
    
    # 检查本地 APK
    apk_path = os.path.join(os.path.dirname(__file__), 'dist', 'VpnProxyClient-debug.apk')
    if not os.path.exists(apk_path):
        print(f"错误: APK 文件不存在: {apk_path}")
        return False
    
    apk_size = os.path.getsize(apk_path) // 1024 // 1024
    print(f"APK 文件: {apk_path}")
    print(f"文件大小: {apk_size} MB")
    
    # 检查服务器连接
    server_ip = "104.244.90.202"
    print(f"\n目标服务器: {server_ip}")
    
    # 生成部署命令
    print("\n=== 部署步骤 ===")
    print("1. SSH 登录服务器:")
    print(f"   ssh root@{server_ip}")
    print()
    print("2. 在服务器上创建目录:")
    print("   mkdir -p /opt/vpn-proxy-apk")
    print()
    print("3. 上传 APK 文件 (从本地执行):")
    print(f"   scp \"{apk_path}\" root@{server_ip}:/opt/vpn-proxy-apk/VpnProxyClient.apk")
    print()
    print("4. 在服务器上启动 HTTP 服务:")
    print("   cd /opt/vpn-proxy-apk")
    print("   python3 -m http.server 18080 &")
    print()
    print("5. 验证服务:")
    print(f"   curl http://{server_ip}:18080/")
    print()
    print("=== 下载地址 ===")
    print(f"   http://{server_ip}:18080/VpnProxyClient.apk")
    
    return True

def create_server_script():
    """创建服务器端部署脚本"""
    script_content = """#!/bin/bash
# 服务器端 APK 部署脚本

SERVER_PORT=18080
APK_DIR="/opt/vpn-proxy-apk"
APK_FILE="$APK_DIR/VpnProxyClient.apk"

# 创建目录
mkdir -p $APK_DIR

# 检查是否已有服务运行
if lsof -i :$SERVER_PORT > /dev/null 2>&1; then
    echo "端口 $SERVER_PORT 已被占用，停止现有服务..."
    fuser -k $SERVER_PORT/tcp
    sleep 2
fi

# 启动 HTTP 服务
echo "启动 HTTP 服务在端口 $SERVER_PORT..."
cd $APK_DIR
nohup python3 -m http.server $SERVER_PORT > /var/log/apk-server.log 2>&1 &

# 显示状态
sleep 2
echo "服务状态:"
ps aux | grep "http.server" | grep -v grep
echo ""
echo "下载地址:"
echo "http://$(curl -s ifconfig.me):$SERVER_PORT/VpnProxyClient.apk"
echo "或"
echo "http://$(hostname -I | awk '{print $1}'):$SERVER_PORT/VpnProxyClient.apk"
"""
    
    script_path = os.path.join(os.path.dirname(__file__), 'deploy_apk_server.sh')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"已创建服务器部署脚本: {script_path}")
    return script_path

if __name__ == "__main__":
    if deploy_to_server():
        script_path = create_server_script()
        print(f"\n✅ 部署准备完成!")
        print(f"1. 将 {script_path} 上传到服务器")
        print(f"2. 在服务器上执行: bash deploy_apk_server.sh")
        print(f"3. APK 下载地址: http://104.244.90.202:18080/VpnProxyClient.apk")