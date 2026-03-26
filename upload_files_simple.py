#!/usr/bin/env python3
"""
简单版本：上传所有文件到服务器
"""
import paramiko
import os
import sys

def main():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 上传 VPNProxy 文件 ===")
        
        # 清理并重新创建目录
        print("1. 准备目录...")
        client.exec_command("rm -rf /opt/vpn-proxy-client/vpnproxy", timeout=30)
        client.exec_command("mkdir -p /opt/vpn-proxy-client/vpnproxy", timeout=30)
        
        # 上传所有文件
        print("2. 上传文件...")
        sftp = client.open_sftp()
        
        # 需要上传的文件列表
        files_to_upload = []
        
        # vpnproxy 目录下的所有 .py 文件
        for filename in os.listdir("vpnproxy"):
            if filename.endswith(".py"):
                files_to_upload.append(("vpnproxy", filename))
        
        # 检查是否有其他必要的文件
        for module in ["client", "protocol", "server", "socks5", "tunnel"]:
            filename = f"{module}.py"
            if os.path.exists(os.path.join("vpnproxy", filename)):
                files_to_upload.append(("vpnproxy", filename))
        
        # 上传文件
        uploaded = 0
        for dirname, filename in files_to_upload:
            local_path = os.path.join(dirname, filename)
            remote_path = f"/opt/vpn-proxy-client/{dirname}/{filename}"
            
            if os.path.exists(local_path):
                sftp.put(local_path, remote_path)
                print(f"  上传: {filename}")
                uploaded += 1
        
        sftp.close()
        print(f"上传完成: {uploaded} 个文件")
        
        # 验证
        print("3. 验证文件...")
        stdin, stdout, stderr = client.exec_command("find /opt/vpn-proxy-client/vpnproxy -name '*.py' | wc -l", timeout=30)
        file_count = stdout.read().decode().strip()
        print(f"服务器上的 .py 文件数量: {file_count}")
        
        # 测试导入
        print("4. 测试导入...")
        test_cmd = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH
python3 -c "
try:
    from vpnproxy.auth_store import AuthStore
    print('IMPORT_OK: auth_store 导入成功')
except ImportError as e:
    print('IMPORT_ERROR:', e)
"
"""
        
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        import_result = stdout.read().decode().strip()
        print(f"导入测试: {import_result}")
        
        if "IMPORT_OK" in import_result:
            print("SUCCESS: 模块导入成功!")
            
            # 启动服务器
            print("5. 启动服务器...")
            start_cmd = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH

# 停止现有
pkill -f 'python.*run.py' 2>/dev/null
sleep 2

# 启动
nohup python3 -u server/run.py > /var/log/vpn-server.log 2>&1 &
echo $! > /tmp/vpn-server.pid
sleep 5

# 检查
if ss -tlnp | grep -q ':18443 '; then
    echo 'SERVER_OK: 端口监听正常'
    ss -tlnp | grep ':18443 '
else
    echo 'SERVER_ERROR: 端口未监听'
    tail -10 /var/log/vpn-server.log
fi
"""
            
            stdin, stdout, stderr = client.exec_command(start_cmd, timeout=60)
            server_result = stdout.read().decode().strip()
            print(f"服务器启动结果:\n{server_result}")
            
            if "SERVER_OK" in server_result:
                print("\n" + "="*60)
                print("SUCCESS: VPN 服务器运行正常!")
                print("="*60)
                print("地址: 104.244.90.202:18443")
                print("账号: demo / demo123")
                print("="*60)
                return True
            else:
                print("ERROR: 服务器启动失败")
                return False
        else:
            print("ERROR: 模块导入失败")
            return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)