# 模拟器测试脚本
# 1. 检查环境
Write-Host "检查 Android 环境..."
if (Test-Path "E:\work\tools\android-sdk\emulator\emulator.exe") {
    Write-Host "? 模拟器可执行文件存在"
} else {
    Write-Host "? 模拟器可执行文件未找到"
}

# 2. 检查 AVD
Write-Host "
检查 AVD..."
\ = & "E:\work\tools\android-sdk\emulator\emulator.exe" -list-avds 2>&1
if (\ -and \ -notmatch "ERROR") {
    Write-Host "? 找到 AVD:"
    \
} else {
    Write-Host "? 没有可用的 AVD"
}

# 3. 尝试启动模拟器（不等待）
Write-Host "
尝试启动模拟器..."
try {
    Start-Process "E:\work\tools\android-sdk\emulator\emulator.exe" -ArgumentList "@vpnproxy_e2e", "-no-snapshot", "-no-audio", "-no-boot-anim", "-memory", "2048" -NoNewWindow
    Write-Host "? 模拟器启动命令已发送"
} catch {
    Write-Host "? 启动失败: \"
}
