import paramiko
import os

def upload_apk():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    local_apk = r"E:\work\vpn-proxy-client\downloaded_apk\VpnProxyClient_with_logs_20260324_182446.apk"
    remote_dir = "/opt/vpn-proxy-apk"
    
    # 要上传的文件
    files_to_upload = [
        (local_apk, f"{remote_dir}/VpnProxyClient.apk"),
        (local_apk, f"{remote_dir}/VpnProxyClient_with_logs_20260324_182446.apk")
    ]
    
    try:
        print("连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("上传文件...")
        sftp = client.open_sftp()
        
        for local_path, remote_path in files_to_upload:
            filename = os.path.basename(local_path)
            print(f"  上传: {filename} -> {remote_path}")
            sftp.put(local_path, remote_path)
        
        sftp.close()
        
        # 验证上传
        print("验证上传...")
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_dir}/*.apk | grep '20260324_182446\|VpnProxyClient.apk'")
        result = stdout.read().decode().strip()
        print(f"服务器文件列表:\n{result}")
        
        # 测试下载
        print("测试下载链接...")
        test_url = f"http://localhost:18080/{serverLoggedApk}"
        stdin, stdout, stderr = client.exec_command(f"curl -I {test_url}")
        http_result = stdout.read().decode().strip()
        
        if "200 OK" in http_result:
            print(f"SUCCESS: 文件可访问")
        else:
            print(f"WARNING: {http_result}")
        
        client.close()
        print("上传完成!")
        
    except Exception as e:
        print(f"上传失败: {e}")

if __name__ == "__main__":
    upload_apk()
