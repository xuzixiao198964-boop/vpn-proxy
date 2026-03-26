# 重新构建带时间戳的 APK
$ErrorActionPreference = "Stop"

# 设置环境变量
$env:ANDROID_HOME = "E:\work\tools\android-sdk"
$env:JAVA_HOME = "E:\work\tools\jdk17-extract\jdk-17.0.18+8"

Write-Host "=== 重新构建 APK（带时间戳） ==="
Write-Host "Android SDK: $env:ANDROID_HOME"
Write-Host "Java JDK: $env:JAVA_HOME"

# 清理旧的构建
Write-Host "`n清理旧的构建文件..."
Remove-Item -Path "android\app\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "android\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist\*" -Recurse -Force -ErrorAction SilentlyContinue

# 生成时间戳
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "时间戳: $timestamp"

# 构建 APK
Write-Host "`n开始构建 APK..."
cd android

try {
    # 执行 Gradle 构建
    .\gradlew.bat clean assembleDebug
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "APK 构建成功!"
        
        # 原始 APK 路径
        $originalApk = "app\build\outputs\apk\debug\app-debug.apk"
        
        if (Test-Path $originalApk) {
            # 创建 dist 目录
            New-Item -ItemType Directory -Path "..\dist" -Force
            
            # 带时间戳的新文件名
            $newApkName = "VpnProxyClient_${timestamp}.apk"
            $newApkPath = "..\dist\$newApkName"
            
            # 复制并重命名
            Copy-Item -Path $originalApk -Destination $newApkPath -Force
            
            # 检查文件
            $fileInfo = Get-Item $newApkPath
            $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
            
            Write-Host "`nSUCCESS: APK 生成完成!"
            Write-Host "文件名: $newApkName"
            Write-Host "文件大小: $sizeMB MB"
            Write-Host "路径: $newApkPath"
            
            # 创建不带时间戳的副本（用于服务器）
            $serverApkPath = "..\dist\VpnProxyClient.apk"
            Copy-Item -Path $newApkPath -Destination $serverApkPath -Force
            Write-Host "服务器副本: $serverApkPath"
            
            return $true
        } else {
            Write-Host "ERROR: APK 文件未找到: $originalApk"
            return $false
        }
    } else {
        Write-Host "ERROR: Gradle 构建失败"
        return $false
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    return $false
} finally {
    cd ..
}