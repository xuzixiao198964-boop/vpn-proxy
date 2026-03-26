# 在 Android 模拟器上安装 APK（需本机已具备 CPU 加速：AEHD 或 WHPX）
# 首次在 Windows 上请以管理员身份运行：
#   E:\work\tools\android-sdk\extras\google\Android_Emulator_Hypervisor_Driver\silent_install.bat
# AVD 数据目录建议使用 E: 盘（已设置 ANDROID_SDK_HOME=E:\work\android_sdk_home）
$ErrorActionPreference = "Stop"
$env:ANDROID_SDK_HOME = "E:\work\android_sdk_home"
$env:ANDROID_HOME = "E:\work\tools\android-sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:JAVA_HOME = "E:\work\tools\jdk17-extract\jdk-17.0.18+8"
$env:Path = "E:\work\tools\android-sdk\emulator;E:\work\tools\android-sdk\platform-tools;$env:Path"

$root = Split-Path $PSScriptRoot -Parent
$apk = Join-Path $root "dist\VpnProxyClient-debug.apk"
if (-not (Test-Path $apk)) {
    $apk = Join-Path $root "android\app\build\outputs\apk\debug\app-debug.apk"
}

Write-Host "启动模拟器 vpnproxy_e2e（无头）…"
Start-Process -FilePath "E:\work\tools\android-sdk\emulator\emulator.exe" -ArgumentList @(
    "-avd", "vpnproxy_e2e",
    "-no-snapshot-load", "-no-audio", "-gpu", "swiftshader_indirect",
    "-no-boot-anim", "-no-window", "-no-metrics"
) -WindowStyle Hidden

$deadline = (Get-Date).AddMinutes(12)
do {
    $lines = adb devices
    $dev = ($lines | Select-String "emulator-\d+\s+device")
    if ($dev) {
        $bc = adb shell getprop sys.boot_completed 2>$null
        if ($bc -match "1") { break }
    }
    Start-Sleep -Seconds 5
    Write-Host "等待设备就绪…"
} while ((Get-Date) -lt $deadline)

$online = adb devices | Select-String "device$"
if (-not $online) {
    Write-Error "未检测到 online 设备。请安装 AEHD/WHPX 后重试，或见 USAGE.md「模拟器」说明。"
    exit 1
}

Write-Host "安装 APK…"
adb install -r $apk
adb shell pm list packages | Select-String "vpnproxy"
Write-Host "EMULATOR_E2E_OK"
