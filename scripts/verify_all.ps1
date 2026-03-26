# 一键验证：Python 依赖、隧道脚本、Android 构建、aapt 包信息、lint
# 用法（PowerShell）：cd vpn-proxy-client ; powershell -ExecutionPolicy Bypass -File scripts\verify_all.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "== [1/5] pip install =="
python -m pip install -q -U pip
pip install -q -r requirements-all.txt requests pysocks

Write-Host "== [2/5] scripts\verify_local.py =="
python scripts\verify_local.py
if ($LASTEXITCODE -ne 0) { throw "verify_local failed" }

Write-Host "== [3/5] gradlew assembleDebug + lint =="
$env:JAVA_HOME = "E:\work\tools\jdk17-extract\jdk-17.0.18+8"
$env:ANDROID_HOME = "E:\work\tools\android-sdk"
Push-Location android
.\gradlew.bat :app:assembleDebug :app:lintDebug --no-daemon -q
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "gradle failed" }
Pop-Location

Write-Host "== [4/5] aapt badging =="
$aapt = "E:\work\tools\android-sdk\build-tools\34.0.0\aapt.exe"
$apk = Join-Path $root "dist\VpnProxyClient-debug.apk"
if (-not (Test-Path $apk)) {
    Copy-Item (Join-Path $root "android\app\build\outputs\apk\debug\app-debug.apk") $apk -Force
}
& $aapt dump badging $apk | Select-Object -First 3

Write-Host "== [5/5] done =="
Write-Host "ALL_CHECKS_OK"
