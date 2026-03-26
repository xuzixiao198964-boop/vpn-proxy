@echo off
echo ========================================
echo ???APK????
echo ========================================
echo.

echo [1] ?????...
"E:\work\tools\android-sdk\emulator\emulator.exe" -avd vpnproxy_x86_64 -no-snapshot -no-audio -no-boot-anim -memory 1024 -accel off

echo.
echo [2] ??60???????...
timeout /t 60 /nobreak >nul

echo.
echo [3] ??ADB??...
"E:\work\tools\android-sdk\platform-tools\adb.exe" devices

echo.
echo [4] ???????APK...
"E:\work\tools\android-sdk\platform-tools\adb.exe" install "dist\VpnProxyClient_LOGS_IN_APP_20260325_091059.apk"

echo.
echo [5] ????...
"E:\work\tools\android-sdk\platform-tools\adb.exe" shell am start -n "com.vpnproxy.app/.MainActivity"

echo.
echo [6] ??????...
"E:\work\tools\android-sdk\platform-tools\adb.exe" logcat -d | findstr /i "vpnproxy|com.vpnproxy" | head -20

echo.
echo ========================================
echo ?????
echo ========================================
echo.
pause
