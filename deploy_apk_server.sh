#!/bin/bash
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
