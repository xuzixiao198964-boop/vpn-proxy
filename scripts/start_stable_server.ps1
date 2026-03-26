#!/usr/bin/env pwsh
# 启动稳定的 HTTP 服务器

$ServerIP = "104.244.90.202"
$Username = "root"
$Password = "v9wSxMxg92dp"

Write-Host "🚀 启动稳定的 HTTP 服务器..." -ForegroundColor Yellow

# 通过 SSH 执行命令
$SSH_Command = @"
# 停止所有占用 11000 端口的进程
pkill -f "http.server.*11000" 2>/dev/null || true
pkill -f "python.*11000" 2>/dev/null || true

# 确保 APK 文件存在
if [ ! -f "/opt/downloads/VpnProxyClient-debug.apk" ]; then
    echo "❌ APK 文件不存在"
    exit 1
fi

# 复制到 /tmp 目录（使用现有 18080 端口服务器）
cp /opt/downloads/VpnProxyClient-debug.apk /tmp/
cp /opt/downloads/test.txt /tmp/

echo "✅ 文件已复制到 /tmp/"
echo ""
echo "📥 下载链接:"
echo "http://${ServerIP}:18080/VpnProxyClient-debug.apk"
echo ""
echo "📄 测试链接:"
echo "http://${ServerIP}:18080/test.txt"
echo ""
echo "📊 文件信息:"
ls -lh /tmp/VpnProxyClient-debug.apk
"@

# 保存到临时文件
$TempFile = "E:\work\vpn-proxy-client\temp\ssh_command.sh"
New-Item -ItemType Directory -Force -Path "E:\work\vpn-proxy-client\temp" | Out-Null
$SSH_Command | Out-File -FilePath $TempFile -Encoding UTF8

Write-Host "执行 SSH 命令..." -ForegroundColor Cyan

# 使用 plink 执行 SSH 命令
$PlinkPath = "E:\work\tools\plink.exe"
if (Test-Path $PlinkPath) {
    & $PlinkPath -ssh -pw $Password "${Username}@${ServerIP}" -m $TempFile
} else {
    Write-Host "使用 Python SSH 执行..." -ForegroundColor Yellow
    cd E:\work\vpn-proxy-client\tools
    python -c "
import paramiko
import sys

host = '$ServerIP'
username = '$Username'
password = '$Password'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(host, 22, username, password, timeout=10)
    stdin, stdout, stderr = client.exec_command('bash -s', timeout=30)
    stdin.write('''$SSH_Command''')
    stdin.close()
    
    print(stdout.read().decode())
    print(stderr.read().decode())
except Exception as e:
    print(f'SSH 错误: {e}')
finally:
    client.close()
"
}

Write-Host ""
Write-Host "🎯 如果上述方法失败，请手动操作:" -ForegroundColor Red
Write-Host "1. SSH 登录服务器: ssh ${Username}@${ServerIP}" -ForegroundColor Yellow
Write-Host "2. 密码: $Password" -ForegroundColor Yellow
Write-Host "3. 执行命令:" -ForegroundColor Yellow
Write-Host "   cd /opt/downloads" -ForegroundColor White
Write-Host "   python3 -m http.server 11000 --bind 0.0.0.0" -ForegroundColor White
Write-Host ""
Write-Host "4. 测试链接:" -ForegroundColor Green
Write-Host "   http://${ServerIP}:11000/VpnProxyClient-debug.apk" -ForegroundColor Cyan