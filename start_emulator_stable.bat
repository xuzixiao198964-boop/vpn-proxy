@echo off
echo ========================================
echo 稳定启动模拟器
echo ========================================
echo.

set ADB_PATH=E:\work\tools\android-sdk\platform-tools\adb.exe
set EMULATOR_PATH=E:\work\tools\android-sdk\emulator\emulator.exe
set AVD_NAME=vpnproxy_x86_64

echo [1] 停止所有模拟器实例...
%ADB_PATH% kill-server
taskkill /F /IM qemu-system-x86_64.exe 2>nul
taskkill /F /IM emulator.exe 2>nul

echo [2] 启动ADB服务...
%ADB_PATH% start-server

echo [3] 启动模拟器（软件渲染模式）...
start "" "%EMULATOR_PATH%" -avd %AVD_NAME% -no-snapshot -no-audio -no-boot-anim -memory 1024 -accel off -gpu swiftshader -no-window

echo [4] 等待60秒让模拟器启动...
timeout /t 60 /nobreak >nul

echo [5] 检查设备状态...
%ADB_PATH% devices

echo [6] 等待设备完全就绪...
for /L %%i in (1,1,10) do (
    %ADB_PATH% shell getprop sys.boot_completed 2>nul | findstr "1" >nul
    if not errorlevel 1 (
        echo 设备已就绪！
        goto :READY
    )
    echo 等待... (%%i/10)
    timeout /t 5 /nobreak >nul
)

echo 设备可能未完全启动，继续测试...
:READY

echo.
echo ========================================
echo 模拟器启动完成
echo ========================================
echo.
pause