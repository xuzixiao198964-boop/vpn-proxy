# 构建带日志功能的 APK

$ErrorActionPreference = "Stop"

Write-Host "=== 构建带日志功能的 APK ==="
Write-Host "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# 1. 检查环境
Write-Host "1. 检查构建环境..."
$javaHome = "E:\work\tools\jdk17-extract\jdk-17.0.18+8"
$env:JAVA_HOME = $javaHome
$env:PATH = "$javaHome\bin;$env:PATH"

Write-Host "   Java 版本:"
java -version
Write-Host ""

# 2. 更新 Gradle 配置
Write-Host "2. 更新 Gradle 配置..."
$gradleWrapper = "android\gradle\wrapper\gradle-wrapper.properties"
if (Test-Path $gradleWrapper) {
    (Get-Content $gradleWrapper) -replace "gradle-8\.[0-9]+-all\.zip", "gradle-8.9-all.zip" | Set-Content $gradleWrapper
    Write-Host "   Gradle 版本已更新为 8.9"
} else {
    Write-Host "   警告: gradle-wrapper.properties 未找到"
}
Write-Host ""

# 3. 备份原始文件
Write-Host "3. 备份原始文件..."
$backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

$filesToBackup = @(
    "android\app\src\main\java\com\vpnproxy\app\MainActivity.kt",
    "android\app\src\main\java\com\vpnproxy\app\TunVpnService.kt"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        $backupPath = Join-Path $backupDir (Split-Path $file -Leaf)
        Copy-Item -Path $file -Destination $backupPath -Force
        Write-Host "   已备份: $file"
    }
}
Write-Host ""

# 4. 替换为增强版文件
Write-Host "4. 替换为增强版文件..."
$enhancedFiles = @{
    "EnhancedMainActivity.kt" = "MainActivity.kt"
    "EnhancedTunVpnService.kt" = "TunVpnService.kt"
    "SelectableLogUtils.kt" = "SelectableLogUtils.kt"
    "SelectableLogActivity.kt" = "SelectableLogActivity.kt"
}

foreach ($source in $enhancedFiles.Keys) {
    $target = $enhancedFiles[$source]
    $sourcePath = "android\app\src\main\java\com\vpnproxy\app\$source"
    $targetPath = "android\app\src\main\java\com\vpnproxy\app\$target"
    
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $targetPath -Force
        Write-Host "   已复制: $source -> $target"
    } else {
        Write-Host "   警告: $source 未找到"
    }
}
Write-Host ""

# 5. 复制布局文件
Write-Host "5. 复制布局文件..."
$layoutFiles = @(
    "activity_selectable_log.xml",
    "log_menu.xml"
)

foreach ($layout in $layoutFiles) {
    $sourcePath = "android\app\src\main\res\layout\$layout"
    $targetPath = "android\app\src\main\res\layout\$layout"
    
    if (Test-Path $sourcePath) {
        Write-Host "   布局文件: $layout (已存在)"
    } else {
        Write-Host "   警告: $layout 未找到"
    }
}
Write-Host ""

# 6. 更新 AndroidManifest.xml
Write-Host "6. 更新 AndroidManifest.xml..."
$manifestPath = "android\app\src\main\AndroidManifest.xml"
if (Test-Path $manifestPath) {
    $manifestContent = Get-Content $manifestPath -Raw
    
    # 添加 SelectableLogActivity
    if ($manifestContent -notmatch "SelectableLogActivity") {
        $newManifest = $manifestContent -replace 
            '<activity android:name="\.MainActivity"',
            '<activity android:name=".SelectableLogActivity"
            android:label="VPN 日志"
            android:exported="false" />
        <activity android:name=".MainActivity"'
        
        Set-Content -Path $manifestPath -Value $newManifest -Encoding UTF8
        Write-Host "   AndroidManifest.xml 已更新"
    } else {
        Write-Host "   AndroidManifest.xml 已包含 SelectableLogActivity"
    }
} else {
    Write-Host "   错误: AndroidManifest.xml 未找到"
}
Write-Host ""

# 7. 构建 APK
Write-Host "7. 开始构建 APK..."
cd android

try {
    # 清理
    Write-Host "   清理构建..."
    .\gradlew.bat clean
    
    # 构建调试版
    Write-Host "   构建调试版 APK..."
    .\gradlew.bat assembleDebug --no-daemon --stacktrace
    
    # 检查构建结果
    $apkPath = "app\build\outputs\apk\debug\app-debug.apk"
    if (Test-Path $apkPath) {
        $fileInfo = Get-Item $apkPath
        $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        
        Write-Host "   SUCCESS: APK 构建成功!"
        Write-Host "   文件: $apkPath"
        Write-Host "   大小: $sizeMB MB"
        Write-Host "   时间: $(Get-Date -Format 'HH:mm:ss')"
        
        # 复制到 dist 目录
        $distDir = "..\dist"
        New-Item -ItemType Directory -Path $distDir -Force
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $distApk = "$distDir\VpnProxyClient_with_selectable_logs_$timestamp.apk"
        Copy-Item -Path $apkPath -Destination $distApk -Force
        
        Write-Host "   已复制到: $distApk"
        
        # 生成版本信息
        $versionInfo = @"
=== VPN Proxy Client with Selectable Logs ===
构建时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
时间戳: $timestamp
文件: $(Split-Path $distApk -Leaf)
大小: $sizeMB MB

包含功能:
1. 可选择、可复制的日志系统
2. 增强的停止功能
3. 状态一致性修复
4. 详细的诊断报告
5. 改进的 UI 状态显示

下载地址:
http://104.244.90.202:18080/$(Split-Path $distApk -Leaf)
"@
        
        Set-Content -Path "$distDir\VERSION_$timestamp.txt" -Value $versionInfo
        
    } else {
        Write-Host "   错误: APK 文件未生成"
    }
    
} catch {
    Write-Host "   构建失败: $_"
    Write-Host "   错误详情请查看上面的日志"
}

cd ..
Write-Host ""

# 8. 恢复原始文件（可选）
Write-Host "8. 恢复原始文件..."
$restoreChoice = Read-Host "是否恢复原始文件? (y/n)"
if ($restoreChoice -eq "y") {
    foreach ($file in $filesToBackup) {
        $backupPath = Join-Path $backupDir (Split-Path $file -Leaf)
        if (Test-Path $backupPath) {
            Copy-Item -Path $backupPath -Destination $file -Force
            Write-Host "   已恢复: $file"
        }
    }
} else {
    Write-Host "   保留增强版文件"
}
Write-Host ""

Write-Host "=== 构建完成 ==="
Write-Host "请检查构建结果并上传到服务器"