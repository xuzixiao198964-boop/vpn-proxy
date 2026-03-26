# 上传 APK 到服务器脚本
param(
    [string]$Server = "104.244.90.202",
    [string]$User = "root",
    [string]$LocalApk = "dist\VpnProxyClient-debug.apk",
    [string]$RemotePath = "/opt/vpn-proxy-apk"
)

Write-Host "=== APK 上传脚本 ==="
Write-Host "服务器: ${User}@${Server}"
Write-Host "本地 APK: $LocalApk"
Write-Host "远程路径: $RemotePath"

# 检查本地文件
if (-not (Test-Path $LocalApk)) {
    Write-Host "错误: APK 文件不存在: $LocalApk" -ForegroundColor Red
    exit 1
}

$apkSize = (Get-Item $LocalApk).Length / 1MB
Write-Host "APK 大小: $([math]::Round($apkSize, 2)) MB"

# 使用 OpenSSH
$sshPath = "E:\work\tools\OpenSSH-Win64\OpenSSH-Win64\ssh.exe"
$scpPath = "E:\work\tools\OpenSSH-Win64\OpenSSH-Win64\scp.exe"

if (-not (Test-Path $scpPath)) {
    Write-Host "错误: SCP 未找到: $scpPath" -ForegroundColor Red
    exit 1
}

Write-Host "`n执行命令:"
Write-Host "1. 创建远程目录: ssh ${User}@${Server} 'mkdir -p $RemotePath'"
Write-Host "2. 上传 APK: scp '$LocalApk' ${User}@${Server}:${RemotePath}/VpnProxyClient.apk"
Write-Host "3. 验证上传: ssh ${User}@${Server} 'ls -lh $RemotePath/'"

Write-Host "`n请手动执行以上命令（需要密码）"
Write-Host "或提供密码给我自动执行"

# 如果提供密码，可以自动执行
if ($args.Count -gt 0 -and $args[0] -eq "-auto") {
    $password = Read-Host "输入服务器密码" -AsSecureString
    # 这里需要将安全字符串转换为明文（实际使用中不推荐）
    Write-Host "注意: 自动模式需要处理密码安全，建议手动执行"
}