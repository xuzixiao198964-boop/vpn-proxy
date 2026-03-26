# 验证现有 APK 的脚本
$ErrorActionPreference = "Stop"

Write-Host "=== 验证现有 APK ==="

# 检查现有的 APK 文件
$apkFiles = Get-ChildItem -Path "dist" -Filter "*.apk" | Sort-Object LastWriteTime -Descending

if ($apkFiles.Count -eq 0) {
    Write-Host "错误: 没有找到 APK 文件"
    exit 1
}

Write-Host "找到的 APK 文件:"
foreach ($apk in $apkFiles) {
    $sizeMB = [math]::Round($apk.Length / 1MB, 2)
    Write-Host "  $($apk.Name) ($sizeMB MB) - $($apk.LastWriteTime)"
}

$latestApk = $apkFiles[0]
Write-Host "`n使用最新的 APK: $($latestApk.Name)"

# 检查 APK 基本信息
Write-Host "`n检查 APK 基本信息..."
try {
    # 使用 aapt 检查 APK
    $aaptPath = "E:\work\tools\android-sdk\build-tools\34.0.0\aapt.exe"
    if (Test-Path $aaptPath) {
        Write-Host "使用 aapt 检查 APK..."
        & $aaptPath dump badging $latestApk.FullName | Select-String -Pattern "package:|application-label:|sdkVersion:|targetSdkVersion:" | Select-Object -First 10
    } else {
        Write-Host "aapt 未找到，跳过详细检查"
    }
} catch {
    Write-Host "aapt 检查失败: $_"
}

# 生成带时间戳的新版本
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$newApkName = "VpnProxyClient_verified_$timestamp.apk"
$newApkPath = Join-Path "dist" $newApkName

Write-Host "`n生成带时间戳的新版本..."
Copy-Item -Path $latestApk.FullName -Destination $newApkPath -Force

# 验证复制
if (Test-Path $newApkPath) {
    $newApk = Get-Item $newApkPath
    $sizeMB = [math]::Round($newApk.Length / 1MB, 2)
    
    Write-Host "SUCCESS: 新 APK 已生成!"
    Write-Host "文件名: $newApkName"
    Write-Host "文件大小: $sizeMB MB"
    Write-Host "路径: $newApkPath"
    
    # 显示所有 APK
    Write-Host "`n当前所有 APK 文件:"
    Get-ChildItem -Path "dist" -Filter "*.apk" | Sort-Object LastWriteTime -Descending | Format-Table Name, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB,2)}}, LastWriteTime -AutoSize
    
    # 准备上传到服务器
    Write-Host "`n=== 准备上传到服务器 ==="
    Write-Host "服务器: 104.244.90.202"
    Write-Host "目标路径: /opt/vpn-proxy-apk/"
    Write-Host "上传命令:"
    Write-Host "scp `"$newApkPath`" root@104.244.90.202:/opt/vpn-proxy-apk/VpnProxyClient.apk"
    Write-Host "`n下载地址: http://104.244.90.202:18080/VpnProxyClient.apk"
} else {
    Write-Host "错误: 新 APK 生成失败"
    exit 1
}