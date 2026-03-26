@echo off
echo ========================================
echo ??x86????????????
echo ========================================
echo.

set SDK_PATH=E:\work\tools\android-sdk
set AVD_NAME=vpnproxy_x86
set SYSTEM_IMAGE=system-images;android-34;google_apis;x86

echo [1] ??x86????...
call "%SDK_PATH%\tools\bin\sdkmanager.bat" --list | findstr "system-images;android-34;google_apis;x86"

echo.
echo [2] ??x86???...
call "%SDK_PATH%\tools\bin\avdmanager.bat" create avd -n %AVD_NAME% -k "%SYSTEM_IMAGE%" -d "pixel_4"

echo.
echo [3] ??????????????...
set AVD_PATH=%USERPROFILE%\.android\avd\%AVD_NAME%.avd\config.ini
if exist "%AVD_PATH%" (
    echo hw.gpu.mode=swiftshader >> "%AVD_PATH%"
    echo hw.gpu.enabled=yes >> "%AVD_PATH%"
    echo hw.cpu.arch=x86 >> "%AVD_PATH%"
)

echo.
echo [4] ??x86???...
"%SDK_PATH%\emulator\emulator.exe" -avd %AVD_NAME% -no-snapshot -no-audio -no-boot-anim

echo.
echo ========================================
echo x86????????
echo ========================================
echo.
pause
