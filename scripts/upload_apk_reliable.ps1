#!/usr/bin/env pwsh
# 可靠的上传脚本 - 分块上传 APK 文件

$ServerIP = "104.244.90.202"
$ServerPort = "22"
$Username = "root"
$Password = "v9wSxMxg92dp"
$LocalAPK = "E:\work\vpn-proxy-client\dist\VpnProxyClient-debug.apk"
$RemoteDir = "/opt/downloads"
$RemoteAPK = "$RemoteDir/VpnProxyClient-debug.apk"

# 检查文件是否存在
if (-not (Test-Path $LocalAPK)) {
    Write-Error "APK 文件不存在: $LocalAPK"
    exit 1
}

$FileSize = (Get-Item $LocalAPK).Length
Write-Host "APK 文件大小: $([math]::Round($FileSize/1MB, 2)) MB" -ForegroundColor Green

# 使用 OpenSSH 的 scp 上传
$OpenSSH_SCP = "E:\work\tools\OpenSSH-Win64\OpenSSH-Win64\scp.exe"

Write-Host "开始上传 APK 文件到服务器..." -ForegroundColor Yellow

# 尝试上传
& $OpenSSH_SCP -o "StrictHostKeyChecking=no" $LocalAPK "${Username}@${ServerIP}:${RemoteAPK}"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 上传成功!" -ForegroundColor Green
    Write-Host ""
    Write-Host "下载链接:" -ForegroundColor Cyan
    Write-Host "http://${ServerIP}:11000/VpnProxyClient-debug.apk" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host ""
    Write-Host "测试链接:" -ForegroundColor Cyan
    Write-Host "http://${ServerIP}:11000/test.txt" -ForegroundColor White -BackgroundColor DarkBlue
} else {
    Write-Host "❌ 上传失败，请手动操作:" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. 登录服务器:" -ForegroundColor Yellow
    Write-Host "   ssh ${Username}@${ServerIP}" -ForegroundColor White
    Write-Host "   密码: $Password" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 下载 APK:" -ForegroundColor Yellow
    Write-Host "   cd $RemoteDir" -ForegroundColor White
    Write-Host "   wget <临时下载链接>" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 验证文件:" -ForegroundColor Yellow
    Write-Host "   ls -lh VpnProxyClient-debug.apk" -ForegroundColor White
}