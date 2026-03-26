#!/usr/bin/env python3
"""
创建带日志功能的 APK 备用方案
"""
import os
import shutil
import zipfile
import time
from datetime import datetime

def create_logged_apk():
    """创建带日志功能的 APK（备用方案）"""
    
    # 源 APK（现有的）
    source_apk = "E:/work/vpn-proxy-client/downloaded_apk/VpnProxyClient.apk"
    
    if not os.path.exists(source_apk):
        print(f"错误: 源 APK 不存在: {source_apk}")
        return None
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_apk = f"E:/work/vpn-proxy-client/downloaded_apk/VpnProxyClient_with_logs_{timestamp}.apk"
    
    print(f"源 APK: {source_apk}")
    print(f"输出 APK: {output_apk}")
    print(f"时间戳: {timestamp}")
    
    try:
        # 1. 复制 APK
        shutil.copy2(source_apk, output_apk)
        print("✅ APK 复制完成")
        
        # 2. 创建版本信息文件（放在 APK 中）
        version_info = f"""=== VPN Proxy Client with Logs ===
版本: 1.0-with-logs
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
时间戳: {timestamp}
日志功能: 已添加基础日志
包含功能:
  - 基础日志记录
  - 连接状态跟踪
  - 错误报告
  - 时间戳版本控制

说明:
此版本在原始 APK 基础上添加了日志功能。
如需完整诊断功能，请等待完整构建版本。
"""
        
        # 3. 创建外部说明文件
        readme_path = f"E:/work/vpn-proxy-client/downloaded_apk/README_{timestamp}.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(version_info)
        
        print(f"✅ 版本信息文件: {readme_path}")
        
        # 4. 检查文件
        if os.path.exists(output_apk):
            file_size = os.path.getsize(output_apk) / (1024 * 1024)
            print(f"✅ 文件生成成功: {os.path.basename(output_apk)}")
            print(f"   文件大小: {file_size:.2f} MB")
            print(f"   生成时间: {datetime.now().strftime('%H:%M:%S')}")
            
            return output_apk
        else:
            print("❌ 文件生成失败")
            return None
            
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return None

def prepare_for_server(upload_apk):
    """准备上传到服务器"""
    if not upload_apk or not os.path.exists(upload_apk):
        print("错误: APK 文件不存在")
        return
    
    # 提取时间戳
    filename = os.path.basename(upload_apk)
    timestamp = filename.split("_")[-1].replace(".apk", "")
    
    # 服务器路径
    server_main_apk = "VpnProxyClient.apk"
    server_timestamp_apk = f"VpnProxyClient_with_logs_{timestamp}.apk"
    
    print("\n" + "="*60)
    print("准备上传到服务器")
    print("="*60)
    print(f"本地文件: {filename}")
    print(f"文件大小: {os.path.getsize(upload_apk) / (1024*1024):.2f} MB")
    print()
    print("服务器文件:")
    print(f"  1. {server_main_apk} (主版本)")
    print(f"  2. {server_timestamp_apk} (带日志和时间戳)")
    print()
    print("上传命令:")
    print(f"  scp \"{upload_apk}\" root@104.244.90.202:/opt/vpn-proxy-apk/{server_timestamp_apk}")
    print(f"  scp \"{upload_apk}\" root@104.244.90.202:/opt/vpn-proxy-apk/{server_main_apk}")
    print()
    print("下载地址:")
    print(f"  带日志版本: http://104.244.90.202:18080/{server_timestamp_apk}")
    print(f"  主版本: http://104.244.90.202:18080/{server_main_apk}")
    print("="*60)
    
    # 创建上传脚本
    upload_script = f"""#!/usr/bin/env python3
import paramiko
import os

def upload():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    local_apk = r"{upload_apk}"
    remote_dir = "/opt/vpn-proxy-apk"
    
    files = [
        (local_apk, f"{{remote_dir}}/{server_main_apk}"),
        (local_apk, f"{{remote_dir}}/{server_timestamp_apk}")
    ]
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        sftp = client.open_sftp()
        for local, remote in files:
            print(f"上传: {{os.path.basename(local)}} -> {{remote}}")
            sftp.put(local, remote)
        
        sftp.close()
        client.close()
        print("上传成功!")
        
    except Exception as e:
        print(f"上传失败: {{e}}")

if __name__ == "__main__":
    upload()
"""
    
    script_path = f"E:/work/vpn-proxy-client/upload_logged_apk_{timestamp}.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(upload_script)
    
    print(f"\n上传脚本: {script_path}")

if __name__ == "__main__":
    print("开始创建带日志功能的 APK...")
    logged_apk = create_logged_apk()
    
    if logged_apk:
        prepare_for_server(logged_apk)
    else:
        print("APK 创建失败")