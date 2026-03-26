#!/usr/bin/env python3
"""
停止 nginx 服务
"""
import paramiko
import time

def stop_nginx():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("停止 nginx 服务...")
        
        # 方法1: 使用 systemctl 停止 nginx
        stdin, stdout, stderr = client.exec_command("systemctl stop nginx", timeout=30)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"输出: {output}")
        if error and "Failed to stop" not in error:
            print(f"错误: {error}")
        
        # 检查是否停止成功
        time.sleep(2)
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':80 '", timeout=30)
        result = stdout.read().decode().strip()
        
        if result:
            print(f"80 端口仍被占用: {result}")
            print("尝试强制停止...")
            # 方法2: 直接 kill nginx 进程
            stdin, stdout, stderr = client.exec_command("pkill -9 nginx", timeout=30)
            time.sleep(1)
            
            # 再次检查
            stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':80 '", timeout=30)
            result = stdout.read().decode().strip()
            
            if result:
                print(f"强制停止后仍占用: {result}")
                return False
            else:
                print("SUCCESS: nginx 已强制停止")
                return True
        else:
            print("SUCCESS: nginx 已正常停止")
            return True
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

def upload_apk():
    """上传 APK 到服务器"""
    import os
    import paramiko
    
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    local_apk = os.path.join(os.path.dirname(__file__), "dist", "VpnProxyClient-debug.apk")
    remote_dir = "/opt/vpn-proxy-apk"
    remote_apk = f"{remote_dir}/VpnProxyClient.apk"
    
    if not os.path.exists(local_apk):
        print(f"错误: APK 文件不存在: {local_apk}")
        return False
    
    apk_size = os.path.getsize(local_apk) // 1024 // 1024
    print(f"APK 文件: {local_apk}")
    print(f"文件大小: {apk_size} MB")
    
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        # 创建远程目录
        print(f"创建远程目录: {remote_dir}")
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}", timeout=30)
        
        # 使用 SFTP 上传文件
        print(f"上传 APK 到服务器...")
        sftp = client.open_sftp()
        sftp.put(local_apk, remote_apk)
        sftp.close()
        
        # 验证上传
        stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_apk}", timeout=30)
        result = stdout.read().decode().strip()
        
        if result:
            print(f"SUCCESS: APK 上传成功: {result}")
            
            # 检查 18080 端口服务
            stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18080 '", timeout=30)
            port_check = stdout.read().decode().strip()
            
            if port_check:
                print(f"18080 端口已占用: {port_check}")
                print("SUCCESS: APK 下载地址: http://104.244.90.202:18080/VpnProxyClient.apk")
            else:
                print("WARNING: 18080 端口未运行，需要启动 HTTP 服务")
                
            return True
        else:
            print("ERROR: APK 上传失败")
            return False
            
    except Exception as e:
        print(f"上传错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("=== 停止 nginx 服务 ===")
    if stop_nginx():
        print("\n=== 上传 APK 到服务器 ===")
        upload_apk()
    else:
        print("无法停止 nginx，跳过 APK 上传")