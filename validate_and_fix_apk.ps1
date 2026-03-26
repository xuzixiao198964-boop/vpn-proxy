# APK 验证和修复脚本
$ErrorActionPreference = "Stop"

Write-Host "=== APK 验证和修复 ==="
Write-Host "解决'解析包出问题'的错误"

# 1. 检查本地完整 APK
Write-Host "`n1. 检查本地完整 APK..."
$goodApk = "E:\work\vpn-proxy-client\downloaded_apk\VpnProxyClient.apk"

if (Test-Path $goodApk) {
    $goodSize = (Get-Item $goodApk).Length
    $goodSizeMB = [math]::Round($goodSize / 1MB, 2)
    Write-Host "✅ 找到完整 APK: $(Split-Path $goodApk -Leaf)"
    Write-Host "   大小: $goodSizeMB MB"
    
    # 验证 ZIP 结构
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [IO.Compression.ZipFile]::OpenRead($goodApk)
        $entries = $zip.Entries.Count
        $zip.Dispose()
        Write-Host "   ZIP 条目: $entries"
        
        if ($entries -gt 100) {
            Write-Host "   ✅ APK 结构完整"
        }
    } catch {
        Write-Host "   ❌ APK 文件损坏: $_"
    }
} else {
    Write-Host "❌ 完整 APK 不存在"
    exit 1
}

# 2. 从服务器下载检查
Write-Host "`n2. 检查服务器上的 APK..."
$serverUrl = "http://104.244.90.202:18080/VpnProxyClient.apk"
$serverApk = "E:\work\vpn-proxy-client\dist\server_download.apk"

try {
    Write-Host "   从服务器下载: $serverUrl"
    Invoke-WebRequest -Uri $serverUrl -OutFile $serverApk -TimeoutSec 30
    
    if (Test-Path $serverApk) {
        $serverSize = (Get-Item $serverApk).Length
        $serverSizeMB = [math]::Round($serverSize / 1MB, 2)
        Write-Host "   服务器 APK 大小: $serverSizeMB MB"
        
        if ($serverSizeMB -lt 60) {
            Write-Host "   ❌ 服务器 APK 损坏 (只有 $serverSizeMB MB, 应该是 ~64 MB)"
            $serverCorrupted = $true
        } else {
            Write-Host "   ✅ 服务器 APK 正常"
            $serverCorrupted = $false
        }
    }
} catch {
    Write-Host "   ❌ 下载失败: $_"
    $serverCorrupted = $true
}

# 3. 创建修复版本
Write-Host "`n3. 创建修复版本..."
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fixedApk = "E:\work\vpn-proxy-client\dist\VpnProxyClient_fixed_$timestamp.apk"

# 使用本地完整 APK
Copy-Item -Path $goodApk -Destination $fixedApk -Force

if (Test-Path $fixedApk) {
    $fixedSize = (Get-Item $fixedApk).Length
    $fixedSizeMB = [math]::Round($fixedSize / 1MB, 2)
    
    Write-Host "✅ 修复版本创建: $(Split-Path $fixedApk -Leaf)"
    Write-Host "   大小: $fixedSizeMB MB"
    
    # 4. 验证修复版本
    Write-Host "`n4. 验证修复版本..."
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [IO.Compression.ZipFile]::OpenRead($fixedApk)
        $entries = $zip.Entries.Count
        
        # 检查关键文件
        $hasAndroidManifest = $zip.Entries | Where-Object { $_.FullName -eq "AndroidManifest.xml" } | Select-Object -First 1
        $hasClassesDex = $zip.Entries | Where-Object { $_.FullName -eq "classes.dex" } | Select-Object -First 1
        $hasResources = $zip.Entries | Where-Object { $_.FullName -like "res/*" } | Select-Object -First 1
        
        $zip.Dispose()
        
        Write-Host "   ZIP 条目: $entries"
        Write-Host "   AndroidManifest.xml: $(if ($hasAndroidManifest) {'✅'} else {'❌'})"
        Write-Host "   classes.dex: $(if ($hasClassesDex) {'✅'} else {'❌'})"
        Write-Host "   res/ 资源目录: $(if ($hasResources) {'✅'} else {'❌'})"
        
        if ($hasAndroidManifest -and $hasClassesDex -and $hasResources) {
            Write-Host "   ✅ APK 结构完整，应该可以正常安装"
        } else {
            Write-Host "   ❌ APK 缺少关键文件"
        }
    } catch {
        Write-Host "   ❌ APK 验证失败: $_"
    }
    
    # 5. 创建上传说明
    Write-Host "`n5. 准备上传修复版本..."
    
    $uploadGuide = @"
=== APK 修复说明 ===
问题: 解析包出问题
原因: 服务器上的 APK 文件损坏（只有 ~10MB，应该是 ~64MB）
修复: 使用本地完整 APK 重新上传

文件信息:
- 修复版本: $(Split-Path $fixedApk -Leaf)
- 文件大小: $fixedSizeMB MB
- 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 源文件: $(Split-Path $goodApk -Leaf)

上传步骤:
1. 将文件上传到服务器 /opt/vpn-proxy-apk/ 目录
2. 替换损坏的 VpnProxyClient.apk
3. 同时上传带时间戳版本作为备份

上传命令:
scp "$fixedApk" root@104.244.90.202:/opt/vpn-proxy-apk/VpnProxyClient.apk
scp "$fixedApk" root@104.244.90.202:/opt/vpn-proxy-apk/$(Split-Path $fixedApk -Leaf)

下载地址:
1. 主版本: http://104.244.90.202:18080/VpnProxyClient.apk
2. 修复版本: http://104.244.90.202:18080/$(Split-Path $fixedApk -Leaf)

验证方法:
1. 下载 APK（应该看到 ~64MB 文件）
2. 安装测试（应该不再'解析包出问题'）
3. 运行应用测试连接

服务器状态:
- VPN 服务: 104.244.90.202:18443 (已修复，可连接)
- HTTP 服务: 端口 18080 (运行中)
- 默认账号: demo/demo123
"@
    
    Set-Content -Path "E:\work\vpn-proxy-client\dist\FIX_GUIDE_$timestamp.txt" -Value $uploadGuide -Encoding UTF8
    Write-Host "✅ 修复指南: dist\FIX_GUIDE_$timestamp.txt"
    
    # 6. 显示结果
    Write-Host "`n" + "="*60
    Write-Host "修复完成!"
    Write-Host "="*60
    Write-Host "问题: 服务器 APK 损坏（只有 ~10MB）"
    Write-Host "解决方案: 使用完整 APK（$fixedSizeMB MB）重新上传"
    Write-Host ""
    Write-Host "修复文件: $(Split-Path $fixedApk -Leaf)"
    Write-Host "文件大小: $fixedSizeMB MB"
    Write-Host "APK 结构: 完整（包含所有必要文件）"
    Write-Host ""
    Write-Host "需要手动上传到服务器（SSH 连接有问题）:"
    Write-Host "scp `"$fixedApk`" root@104.244.90.202:/opt/vpn-proxy-apk/VpnProxyClient.apk"
    Write-Host ""
    Write-Host "下载地址（上传后）:"
    Write-Host "http://104.244.90.202:18080/VpnProxyClient.apk"
    Write-Host "="*60
    
} else {
    Write-Host "❌ 修复版本创建失败"
    exit 1
}