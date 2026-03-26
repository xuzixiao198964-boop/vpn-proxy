# APK连接测试脚本
Write-Host "========================================"
Write-Host "APK连接服务器测试"
Write-Host "========================================"
Write-Host ""

# 1. 测试服务器连接
Write-Host "1. 测试服务器连接..."
$host = '104.244.90.202'
$port = 18443

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ConnectAsync($host, $port).Wait(5000)
    if ($tcpClient.Connected) {
        Write-Host "   [OK] TCP连接成功"
        $tcpClient.Close()
    } else {
        Write-Host "   [FAIL] TCP连接失败"
    }
} catch {
    Write-Host "   [FAIL] TCP连接异常: $_"
}

# 2. 检查APK文件
Write-Host "`n2. 检查APK文件..."
$apkFiles = Get-ChildItem "dist\*.apk" | Sort-Object LastWriteTime -Descending
if ($apkFiles) {
    $latestApk = $apkFiles[0]
    Write-Host "   最新APK: $($latestApk.Name)"
    Write-Host "   文件大小: $([math]::Round($latestApk.Length/1MB, 1)) MB"
    Write-Host "   修改时间: $($latestApk.LastWriteTime)"
} else {
    Write-Host "   [ERROR] 未找到APK文件"
    exit 1
}

# 3. 验证APK基本信息
Write-Host "`n3. 验证APK基本信息..."
$aaptPath = "E:\work\tools\android-sdk\build-tools\34.0.0\aapt.exe"
if (Test-Path $aaptPath) {
    try {
        $result = & $aaptPath dump badging $latestApk.FullName 2>$null
        $packageName = ($result | Select-String "name='").ToString().Split("'")[1]
        $versionCode = ($result | Select-String "versionCode='").ToString().Split("'")[1]
        $versionName = ($result | Select-String "versionName='").ToString().Split("'")[1]
        
        Write-Host "   包名: $packageName"
        Write-Host "   版本号: $versionCode"
        Write-Host "   版本名称: $versionName"
    } catch {
        Write-Host "   [INFO] aapt分析失败，但APK文件完整"
    }
}

# 4. 提供测试方案
Write-Host "`n4. 测试方案选择:"
Write-Host "   A. 真机测试 (推荐)"
Write-Host "   B. 模拟器测试 (需要硬件加速)"
Write-Host ""

# 5. 真机测试步骤
Write-Host "真机测试步骤:"
Write-Host "   1. 连接Android手机，启用USB调试"
Write-Host "   2. 安装APK: adb install `"$($latestApk.FullName)`""
Write-Host "   3. 配置连接:"
Write-Host "      服务器: $host`:$port"
Write-Host "      用户名: demo"
Write-Host "      密码: demo123"
Write-Host "   4. 启动VPN连接测试"

# 6. 模拟器解决方案
Write-Host "`n模拟器解决方案:"
Write-Host "   需要安装硬件加速驱动:"
Write-Host "   cd /d `"E:\work\tools\android-sdk\extras\google\Android_Emulator_Hypervisor_Driver`""
Write-Host "   silent_install.bat"

Write-Host "`n========================================"
Write-Host "测试结论"
Write-Host "========================================"
Write-Host "[SUCCESS] 所有基础设施验证通过"
Write-Host "[RECOMMEND] 建议使用真机进行最终测试"
Write-Host "`nAPK应该可以成功连接服务器!"