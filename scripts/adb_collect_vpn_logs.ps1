# USB 连接手机并开启 USB 调试后运行，收集 VPN 相关 logcat。
# 用法: powershell -ExecutionPolicy Bypass -File scripts\adb_collect_vpn_logs.ps1

$ErrorActionPreference = "Stop"
$adbCmd = Get-Command adb -ErrorAction SilentlyContinue
if ($null -eq $adbCmd) {
    Write-Error "未找到 adb，请将 Android SDK platform-tools 加入 PATH。"
    exit 1
}
$adb = $adbCmd.Source

& $adb devices
$pkg = "com.vpnproxy.app"
& $adb logcat -c
& $adb shell am force-stop $pkg 2>$null
& $adb shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 2>$null | Out-Null
Start-Sleep -Seconds 2
Write-Host "请在手机上点击连接 VPN，等待 15 秒后自动保存日志..."
Start-Sleep -Seconds 15
$out = Join-Path $PSScriptRoot "vpn_logcat.txt"
& $adb logcat -d -v time "*:E" "TunVpnService:D" "AndroidRuntime:E" > $out
Write-Host "已写入: $out"
