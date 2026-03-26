@echo off
echo ========================================
echo ??Android?????????
echo ========================================
echo.

echo ??????????
echo.

echo [1] ??????...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ????????????...
    
    REM ??VBS??????????
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /b
)

echo [2] ??AEHD??...
cd /d "E:\work\tools\android-sdk\extras\google\Android_Emulator_Hypervisor_Driver"
call silent_install.bat

if %errorlevel% equ 0 (
    echo.
    echo ? AEHD???????
) else (
    echo.
    echo ? AEHD??????
)

echo.
echo [3] ??????...
sc query aehd

echo.
echo ========================================
echo ?????
echo ========================================
echo.
pause
