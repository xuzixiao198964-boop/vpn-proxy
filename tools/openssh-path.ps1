# 将微软 Win32-OpenSSH 便携版加入当前 PowerShell 会话的 PATH（免费、官方发行）
$OpenSshBin = "E:\work\tools\OpenSSH-Win64\OpenSSH-Win64"
if (-not (Test-Path "$OpenSshBin\ssh.exe")) {
    Write-Error "未找到 ssh.exe: $OpenSshBin\ssh.exe"
    exit 1
}
$env:Path = "$OpenSshBin;$env:Path"
Write-Host "OpenSSH 已加入 PATH: $OpenSshBin"
Write-Host "示例: ssh -V"
