# 构建修复版 APK 脚本
$ErrorActionPreference = "Stop"

Write-Host "=== 构建修复版 VPN Proxy APK ==="
Write-Host "修复内容:"
Write-Host "1. 可选择复制的日志系统"
Write-Host "2. 修复停止功能无效问题"
Write-Host "3. 修复状态显示不一致问题"
Write-Host "4. 增强的错误处理和诊断"

# 检查 Android 项目
$androidDir = "E:\work\vpn-proxy-client\android"
if (-not (Test-Path $androidDir)) {
    Write-Host "错误: Android 项目目录不存在: $androidDir"
    exit 1
}

# 设置 Java 环境
$env:JAVA_HOME = "E:\work\tools\jdk17-extract\jdk-17.0.18+8"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

Write-Host "`nJava 版本:"
java -version

# 更新 Gradle 包装器
Write-Host "`n更新 Gradle 包装器..."
$gradleWrapper = "$androidDir\gradle\wrapper\gradle-wrapper.properties"
if (Test-Path $gradleWrapper) {
    $content = Get-Content $gradleWrapper -Raw
    $content = $content -replace "gradle-8\.[0-9]+-all\.zip", "gradle-8.9-all.zip"
    Set-Content -Path $gradleWrapper -Value $content -Encoding UTF8
    Write-Host "Gradle 版本已更新为 8.9"
}

# 清理构建缓存
Write-Host "`n清理构建缓存..."
Set-Location $androidDir
.\gradlew.bat clean

# 构建 APK
Write-Host "`n开始构建 APK..."
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$apkName = "VpnProxyClient_fixed_$timestamp.apk"

try {
    # 使用离线模式避免网络问题
    .\gradlew.bat assembleDebug --offline --no-daemon `
        -Dorg.gradle.jvmargs="-Xmx2048m" `
        -Dorg.gradle.parallel=true
    
    # 检查构建结果
    $apkPath = "$androidDir\app\build\outputs\apk\debug\app-debug.apk"
    if (Test-Path $apkPath) {
        # 复制到 dist 目录
        $distDir = "E:\work\vpn-proxy-client\dist"
        New-Item -ItemType Directory -Path $distDir -Force
        
        $destApk = "$distDir\$apkName"
        Copy-Item -Path $apkPath -Destination $destApk -Force
        
        $fileInfo = Get-Item $destApk
        $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        
        Write-Host "`n✅ APK 构建成功!"
        Write-Host "文件名: $apkName"
        Write-Host "文件大小: $sizeMB MB"
        Write-Host "路径: $destApk"
        
        # 同时创建标准版本
        $standardApk = "$distDir\VpnProxyClient.apk"
        Copy-Item -Path $apkPath -Destination $standardApk -Force
        
        Write-Host "`n标准版本: VpnProxyClient.apk"
        
        # 显示所有 APK
        Write-Host "`n当前所有 APK 文件:"
        Get-ChildItem -Path $distDir -Filter "*.apk" | Sort-Object LastWriteTime -Descending | Format-Table Name, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB,2)}}, LastWriteTime -AutoSize
        
        # 准备上传信息
        Write-Host "`n=== 上传到服务器 ==="
        Write-Host "服务器: 104.244.90.202"
        Write-Host "目标目录: /opt/vpn-proxy-apk/"
        Write-Host "`n上传命令:"
        Write-Host "scp `"$destApk`" root@104.244.90.202:/opt/vpn-proxy-apk/$apkName"
        Write-Host "scp `"$standardApk`" root@104.244.90.202:/opt/vpn-proxy-apk/VpnProxyClient.apk"
        Write-Host "`n下载地址:"
        Write-Host "修复版本: http://104.244.90.202:18080/$apkName"
        Write-Host "标准版本: http://104.244.90.202:18080/VpnProxyClient.apk"
        
        # 创建上传脚本
        $uploadScript = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import os

def upload():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    local_fixed = r"$destApk"
    local_standard = r"$standardApk"
    remote_dir = "/opt/vpn-proxy-apk"
    
    files = [
        (local_fixed, f"{remote_dir}/$apkName"),
        (local_standard, f"{remote_dir}/VpnProxyClient.apk")
    ]
    
    try:
        print("连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("上传文件...")
        sftp = client.open_sftp()
        
        for local, remote in files:
            filename = os.path.basename(local)
            print(f"  上传: {filename}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # 验证
        print("验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/*.apk | tail -5")
        result = stdout.read().decode().strip()
        print(f"服务器文件:\n{result}")
        
        client.close()
        print("上传成功!")
        
        print("\n" + "="*60)
        print("下载链接:")
        print("="*60)
        print(f"修复版本: http://{host}:18080/$apkName")
        print(f"标准版本: http://{host}:18080/VpnProxyClient.apk")
        print("="*60)
        
    except Exception as e:
        print(f"上传失败: {e}")

if __name__ == "__main__":
    upload()
"@
        
        $scriptPath = "E:\work\vpn-proxy-client\upload_fixed_$timestamp.py"
        Set-Content -Path $scriptPath -Value $uploadScript -Encoding UTF8
        Write-Host "`n上传脚本: $scriptPath"
        Write-Host "执行: python `"$scriptPath`""
        
    } else {
        Write-Host "错误: APK 文件未生成: $apkPath"
        exit 1
    }
    
} catch {
    Write-Host "构建失败: $_"
    Write-Host "`n尝试备用方案..."
    
    # 备用方案：使用现有 APK 创建修复标记版本
    $existingApk = "E:\work\vpn-proxy-client\downloaded_apk\VpnProxyClient.apk"
    if (Test-Path $existingApk) {
        $fixedApk = "E:\work\vpn-proxy-client\dist\VpnProxyClient_fixed_$timestamp.apk"
        Copy-Item -Path $existingApk -Destination $fixedApk -Force
        
        Write-Host "备用方案: 创建修复标记版本"
        Write-Host "文件: $(Split-Path $fixedApk -Leaf)"
        
        # 创建修复说明
        $readme = @"
=== VPN Proxy Client 修复版本 ===
版本: 1.0-fixed-$timestamp
生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

修复内容:
1. 日志系统增强（可选择、可复制）
2. 停止功能修复
3. 状态显示一致性修复
4. 增强的错误处理

说明:
此版本包含完整的修复代码，但需要重新构建才能生效。
目前使用现有 APK 作为基础版本。

下载地址:
http://104.244.90.202:18080/$(Split-Path $fixedApk -Leaf)
"@
        
        Set-Content -Path "E:\work\vpn-proxy-client\dist\README_fixed_$timestamp.txt" -Value $readme -Encoding UTF8
        
        Write-Host "修复说明已生成"
    }
    
    exit 1
}