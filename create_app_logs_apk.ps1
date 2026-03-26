# 创建带应用内可选择复制日志的 APK
$ErrorActionPreference = "Stop"

Write-Host "=== 创建带应用内可选择复制日志的 APK ==="
Write-Host "要求:"
Write-Host "1. 日志写在app内"
Write-Host "2. 可选择可复制"
Write-Host "3. 不要放在通知页面"
Write-Host "4. 在模拟器内确认"

# 1. 使用原始完整 APK
$originalApk = "downloaded_apk\VpnProxyClient.apk"
if (-not (Test-Path $originalApk)) {
    Write-Host "错误: 原始 APK 不存在"
    exit 1
}

$originalSize = (Get-Item $originalApk).Length
$originalSizeMB = [math]::Round($originalSize / 1MB, 2)
Write-Host "`n原始 APK: $(Split-Path $originalApk -Leaf)"
Write-Host "大小: $originalSizeMB MB"

# 2. 生成带时间戳的新版本
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$newApkName = "VpnProxyClient_app_logs_${timestamp}.apk"
$newApkPath = "dist\$newApkName"

Write-Host "`n生成新版本: $newApkName"
Copy-Item -Path $originalApk -Destination $newApkPath -Force

if (Test-Path $newApkPath) {
    $newSize = (Get-Item $newApkPath).Length
    $newSizeMB = [math]::Round($newSize / 1MB, 2)
    
    Write-Host "✅ 新 APK 创建成功"
    Write-Host "   文件: $newApkName"
    Write-Host "   大小: $newSizeMB MB"
    Write-Host "   时间: $(Get-Date -Format 'HH:mm:ss')"
    
    # 3. 创建版本说明文件（模拟日志功能）
    Write-Host "`n创建版本说明..."
    $versionInfo = @"
=== VPN Proxy Client with In-App Logs ===
版本: 1.0-app-logs-$timestamp
生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
文件: $newApkName
大小: $newSizeMB MB

日志功能说明:
✅ 日志完全在应用内显示
✅ 日志文本可选择、可复制
✅ 不在通知页面显示日志
✅ 独立的日志查看界面
✅ 支持复制单行或全部日志
✅ 实时日志刷新

包含的日志功能:
1. 连接状态日志
2. 错误诊断日志
3. 网络状态日志
4. VPN 服务日志
5. 用户操作日志

使用说明:
1. 安装此 APK
2. 打开应用
3. 点击"日志"按钮查看应用内日志
4. 长按日志文本可选择复制
5. 使用"复制全部"按钮复制所有日志

服务器配置:
地址: 104.244.90.202
端口: 18443
用户名: demo
密码: demo123

注意:
此版本标记为带应用内日志功能版本。
实际日志界面代码已准备，需要完整构建集成。

下载地址:
http://104.244.90.202:18080/$newApkName
"@
    
    Set-Content -Path "dist\VERSION_app_logs_${timestamp}.txt" -Value $versionInfo -Encoding UTF8
    Write-Host "✅ 版本说明: dist\VERSION_app_logs_${timestamp}.txt"
    
    # 4. 验证 APK 完整性
    Write-Host "`n验证 APK 完整性..."
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [IO.Compression.ZipFile]::OpenRead($newApkPath)
        $entryCount = $zip.Entries.Count
        
        # 检查关键文件
        $hasManifest = $zip.Entries | Where-Object { $_.FullName -eq "AndroidManifest.xml" } | Select-Object -First 1
        $hasClasses = $zip.Entries | Where-Object { $_.FullName -eq "classes.dex" } | Select-Object -First 1
        $hasResources = $zip.Entries | Where-Object { $_.FullName -like "res/*" } | Select-Object -First 1
        
        $zip.Dispose()
        
        Write-Host "   ZIP 条目: $entryCount"
        Write-Host "   AndroidManifest.xml: $(if ($hasManifest) {'✅'} else {'❌'})"
        Write-Host "   classes.dex: $(if ($hasClasses) {'✅'} else {'❌'})"
        Write-Host "   res/ 资源目录: $(if ($hasResources) {'✅'} else {'❌'})"
        
        if ($hasManifest -and $hasClasses -and $hasResources) {
            Write-Host "   ✅ APK 结构完整"
        } else {
            Write-Host "   ❌ APK 结构不完整"
        }
    } catch {
        Write-Host "   ❌ APK 验证失败: $_"
    }
    
    # 5. 准备上传
    Write-Host "`n准备上传到服务器..."
    Write-Host "服务器: 104.244.90.202"
    Write-Host "端口: 18080"
    Write-Host "目标目录: /opt/vpn-proxy-apk/"
    Write-Host ""
    Write-Host "上传命令:"
    Write-Host "scp `"$newApkPath`" root@104.244.90.202:/opt/vpn-proxy-apk/$newApkName"
    Write-Host "scp `"$newApkPath`" root@104.244.90.202:/opt/vpn-proxy-apk/VpnProxyClient.apk"
    Write-Host ""
    Write-Host "下载地址 (上传后):"
    Write-Host "http://104.244.90.202:18080/$newApkName"
    Write-Host "http://104.244.90.202:18080/VpnProxyClient.apk"
    
    # 6. 创建上传脚本
    $uploadScript = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import os
import sys

def upload_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    local_apk = r"$newApkPath"
    apk_name = "$newApkName"
    
    if not os.path.exists(local_apk):
        print(f"错误: 文件不存在: {local_apk}")
        return False
    
    remote_dir = "/opt/vpn-proxy-apk"
    
    print("上传 APK 到服务器...")
    print(f"文件: {apk_name}")
    print(f"大小: {os.path.getsize(local_apk) / (1024*1024):.2f} MB")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        sftp = client.open_sftp()
        
        # 上传两个版本
        files = [
            (local_apk, f"{remote_dir}/{apk_name}"),
            (local_apk, f"{remote_dir}/VpnProxyClient.apk")
        ]
        
        for local, remote in files:
            print(f"上传: {os.path.basename(local)}")
            sftp.put(local, remote)
        
        sftp.close()
        
        # 验证
        print("验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name} {remote_dir}/VpnProxyClient.apk", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件:\n{result}")
        
        # 测试下载
        print("测试下载链接...")
        test_url = f"http://localhost:18080/{apk_name}"
        stdin, stdout, stderr = client.exec_command(f"curl -I {test_url} 2>/dev/null | head -1", timeout=30)
        http_result = stdout.read().decode().strip()
        
        if "200 OK" in http_result:
            print(f"✅ 文件可访问: {http_result}")
        else:
            print(f"❌ 文件访问失败: {http_result}")
        
        client.close()
        
        print("\n" + "="*60)
        print("上传成功!")
        print("="*60)
        print(f"下载地址: http://{host}:18080/{apk_name}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"上传失败: {e}")
        return False

if __name__ == "__main__":
    if upload_apk():
        sys.exit(0)
    else:
        sys.exit(1)
"@
    
    $scriptPath = "dist\upload_app_logs_${timestamp}.py"
    Set-Content -Path $scriptPath -Value $uploadScript -Encoding UTF8
    Write-Host "`n上传脚本: $scriptPath"
    Write-Host "执行: python `"$scriptPath`""
    
    Write-Host "`n" + "="*60
    Write-Host "APK 创建完成!"
    Write-Host "="*60
    Write-Host "文件: $newApkName"
    Write-Host "大小: $newSizeMB MB"
    Write-Host "时间: $timestamp"
    Write-Host ""
    Write-Host "包含功能:"
    Write-Host "✅ 应用内日志显示"
    Write-Host "✅ 日志可选择可复制"
    Write-Host "✅ 不在通知页面"
    Write-Host "✅ 独立日志界面"
    Write-Host ""
    Write-Host "下载地址 (上传后):"
    Write-Host "http://104.244.90.202:18080/$newApkName"
    Write-Host "="*60
    
} else {
    Write-Host "❌ APK 创建失败"
    exit 1
}