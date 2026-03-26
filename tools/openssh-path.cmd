@echo off
REM 将微软 Win32-OpenSSH 便携版加入当前 CMD 会话的 PATH（免费、官方发行）
set "OPENSSH_BIN=E:\work\tools\OpenSSH-Win64\OpenSSH-Win64"
if not exist "%OPENSSH_BIN%\ssh.exe" (
  echo [错误] 未找到 ssh.exe: %OPENSSH_BIN%\ssh.exe
  exit /b 1
)
set "PATH=%OPENSSH_BIN%;%PATH%"
echo OpenSSH 已加入 PATH: %OPENSSH_BIN%
echo 示例: ssh -V
exit /b 0
