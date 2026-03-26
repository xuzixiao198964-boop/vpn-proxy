@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 Windows 图形界面客户端...
python -m windows_client.app_gui
if errorlevel 1 pause
