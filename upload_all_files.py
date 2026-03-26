#!/usr/bin/env python3
"""
上传所有缺失的文件到服务器
"""
import paramiko
import os

def upload_all_vpnproxy_files():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 上传所有 VPNProxy 文件 ===")
        
        # 1. 清理并重新创建目录
        print("\n1. 准备目录...")
        client.exec_command("rm -rf /opt/vpn-proxy-client/vpnproxy", timeout=30)
        client.exec_command("mkdir -p /opt/vpn-proxy-client/vpnproxy", timeout=30)
        
        # 2. 上传所有 .py 文件
        print("\n2. 上传所有 Python 文件...")
        sftp = client.open_sftp()
        
        vpnproxy_files = [
            "auth_store.py",
            "cert_util.py", 
            "framing.py",
            "__init__.py",
            "client.py",
            "protocol.py",
            "server.py",
            "socks5.py",
            "tunnel.py"
        ]
        
        uploaded = 0
        for filename in vpnproxy_files:
            local_path = os.path.join("vpnproxy", filename)
            remote_path = f"/opt/vpn-proxy-client/vpnproxy/{filename}"
            
            if os.path.exists(local_path):
                sftp.put(local_path, remote_path)
                print(f"  ✅ 上传: {filename}")
                uploaded += 1
            else:
                print(f"  ⚠️ 文件不存在: {local_path}")
        
        sftp.close()
        print(f"\n上传完成: {uploaded} 个文件")
        
        # 3. 验证上传
        print("\n3. 验证上传...")
        stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/vpnproxy/*.py", timeout=30)
        files_list = stdout.read().decode().strip()
        print(f"服务器上的文件:\n{files_list}")
        
        # 4. 测试导入
        print("\n4. 测试模块导入...")
        test_cmd = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH
python3 -c "
modules = ['auth_store', 'cert_util', 'framing', 'client', 'protocol', 'server', 'socks5', 'tunnel']
for module in modules:
    try:
        __import__(f'vpnproxy.{module}')
        print(f'✅ vpnproxy.{module}: 导入成功')
    except ImportError as e:
        print(f'❌ vpnproxy.{module}: 导入失败 - {e}')
"
"""
        
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        import_test = stdout.read().decode().strip()
        print(f"导入测试结果:\n{import_test}")
        
        return "导入失败" not in import_test
        
    except Exception as e:
        print(f"上传错误: {e}")
        return False
    finally:
        if client:
            client.close()

def start_vpn_server():
    """启动 VPN 服务器"""
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("\n=== 启动 VPN 服务器 ===")
        
        # 停止现有进程
        client.exec_command("pkill -f 'python.*run.py'", timeout=30)
        
        # 启动服务器
        start_script = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH

# 启动
nohup python3 -u server/run.py > /var/log/vpn-server.log 2>&1 &
SERVER_PID=$!
echo "服务器PID: $SERVER_PID"
echo $SERVER_PID > /tmp/vpn-server.pid

# 等待启动
sleep 8

# 检查状态
echo "检查进程..."
ps -p $SERVER_PID >/dev/null && echo "✅ 进程运行中" || echo "❌ 进程已退出"

echo "检查端口..."
ss -tlnp | grep ':18443 ' && echo "✅ 端口监听中" || echo "❌ 端口未监听"

echo "检查日志..."
tail -5 /var/log/vpn-server.log
"""
        
        stdin, stdout, stderr = client.exec_command(start_script, timeout=60)
        output = stdout.read().decode().strip()
        print(f"启动输出:\n{output}")
        
        # 最终验证
        print("\n最终验证...")
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18443 '", timeout=30)
        port_check = stdout.read().decode().strip()
        
        if port_check:
            print(f"✅ VPN 服务器运行正常!")
            print(f"   端口状态: {port_check}")
            
            # 获取证书信息
            stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/server/data/certs/", timeout=30)
            certs = stdout.read().decode().strip()
            print(f"   证书文件:\n{certs}")
            
            return True
        else:
            print("❌ VPN 服务器未运行")
            return False
        
    except Exception as e:
        print(f"启动错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始修复 VPN 服务器...")
    
    # 上传文件
    if upload_all_vpnproxy_files():
        print("\n文件上传成功!")
        
        # 启动服务器
        if start_vpn_server():
            print("\n" + "="*60)
            print("🎉 SUCCESS: VPN 服务器已成功启动!")
            print("="*60)
            print("服务器信息:")
            print("  地址: 104.244.90.202:18443")
            print("  默认账号: demo / demo123")
            print("  日志: /var/log/vpn-server.log")
            print("="*60)
            print("\n下一步:")
            print("1. 下载证书: scp root@104.244.90.202:/opt/vpn-proxy-client/server/data/certs/server.crt .")
            print("2. 更新 APK 中的证书")
            print("3. 重新构建 APK")
            print("4. 在 APK 中添加详细日志功能")
        else:
            print("\n❌ ERROR: 服务器启动失败")
    else:
        print("\n❌ ERROR: 文件上传失败")