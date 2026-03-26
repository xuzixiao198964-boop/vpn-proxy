@echo off
echo ========================================
echo ??x86_64????APK?????
echo ========================================
echo.

echo 1. ??x86_64???...
cd /d "E:\work\tools\android-sdk\emulator"
start emulator.exe -avd vpnproxy_x86_64 -no-snapshot-load

echo.
echo 2. ??30???????...
timeout /t 30 /nobreak

echo.
echo 3. ??APK...
cd /d "E:\work\tools\android-sdk\platform-tools"
adb install "E:\work\vpn-proxy-client\dist\VpnProxyClient_FINAL_FIXED_20260324_223008.apk"

echo.
echo 4. ????...
adb shell am start -n "com.vpnproxy.app/.MainActivity"

echo.
echo 5. ???????...
powershell -Command "Test-NetConnection -ComputerName 104.244.90.202 -Port 18443"

echo.
echo ========================================
echo ?????
echo APK????: http://104.244.90.202:18080/VpnProxyClient_FINAL_FIXED_20260324_223008.apk
echo ???: 104.244.90.202:18443
echo ???: demo
echo ??: demo123
echo ========================================
pause
