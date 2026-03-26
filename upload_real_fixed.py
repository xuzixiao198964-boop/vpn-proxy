#!/usr/bin/env python3
import paramiko
import os
import sys

def upload():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    apk_name = "VpnProxyClient_REAL_NO_NOTIFY_20260324_214911.apk"
    local_apk = r"E:\work\vpn-proxy-client\dist\VpnProxyClient_REAL_NO_NOTIFY_20260324_214911.apk"
    
    if not os.path.exists(local_apk):
        print("文件不存在")
        return False
    
    try:
        print("连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=15)
        
        print("上传文件...")
        sftp = client.open_sftp()
        
        remote_dir = "/opt/vpn-proxy-apk"
        remote_file = f"{remote_dir}/{apk_name}"
        
        sftp.put(local_apk, remote_file)
        print(f"上传: {apk_name}")
        
        # 更新主版本
        remote_main = f"{remote_dir}/VpnProxyClient.apk"
        sftp.put(local_apk, remote_main)
        print("更新主版本")
        
        sftp.close()
        
        # 验证
        print("验证...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/{apk_name}", timeout=30)
        result = stdout.read().decode().strip()
        print(f"服务器文件: {result}")
        
        # 测试下载
        test_url = f"http://localhost:18080/{apk_name}"
        stdin, stdout, stderr = client.exec_command(f"curl -I {test_url} 2>/dev/null | head -1", timeout=30)
        http_result = stdout.read().decode().strip()
        
        if "200 OK" in http_result:
            print("✅ 下载链接可用")
        else:
            print(f"下载测试: {http_result}")
        
        client.close()
        
        print("✅ 上传成功!")
        print(f"地址: http://{host}:18080/{apk_name}")
        return True
        
    except Exception as e:
        print(f"上传失败: {e}")
        return False

if __name__ == "__main__":
    print("上传真正修改的APK...")
    if upload():
        sys.exit(0)
    else:
        sys.exit(1)