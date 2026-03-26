# 将服务端代码同步到 VPS（需本机已可用 ssh/scp）
# 用法: .\deploy_server_to_vps.ps1 -VpsHost "104.x.x.x"
param(
    [Parameter(Mandatory = $true)][string]$VpsHost,
    [string]$VpsUser = "root",
    [string]$RemotePath = "/opt/vpn-proxy-client"
)
$ErrorActionPreference = "Stop"
$here = Split-Path $PSScriptRoot -Parent
$ssh = "ssh"
$scp = "scp"
$openSsh = "E:\work\tools\OpenSSH-Win64\OpenSSH-Win64"
if (Test-Path "$openSsh\ssh.exe") {
    $ssh = "$openSsh\ssh.exe"
    $scp = "$openSsh\scp.exe"
}
Write-Host "上传目录: $here -> ${VpsUser}@${VpsHost}:$RemotePath"
& $scp -r "$here\server" "$here\vpnproxy" "${VpsUser}@${VpsHost}:${RemotePath}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "scp 失败。"
    exit 1
}
Write-Host "完成。在 VPS 上执行:"
Write-Host "  cd $RemotePath && pip3 install -r server/requirements.txt && python3 server/run.py"
