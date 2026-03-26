#!/usr/bin/env python3
"""
完整部署 VPN 服务器
"""
import paramiko
import os
import time

def upload_directory(sftp, local_path, remote_path):
    """上传整个目录"""
    for item in os.listdir(local_path):
        local_item = os.path.join(local_path, item)
        remote_item = os.path.join(remote_path, item)
        
        if os.path.isfile(local_item) and item.endswith('.py'):
            sftp.put(local_item, remote_item)
            print(f"  上传文件: {item}")

def deploy_complete():
    """完整部署"""
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 完整部署 VPN 服务器 ===")
        
        # 创建目录
        print("\n1. 创建目录结构...")
        dirs = [
            "/opt/vpn-proxy-client",
            "/opt/vpn-proxy-client/server",
            "/opt/vpn-proxy-client/vpnproxy",
            "/opt/vpn-proxy-client/server/data",
            "/opt/vpn-proxy-client/server/data/certs"
        ]
        
        for dir_path in dirs:
            stdin, stdout, stderr = client.exec_command(f"mkdir -p {dir_path}", timeout=30)
        
        # 上传文件
        print("\n2. 上传服务器文件...")
        sftp = client.open_sftp()
        
        # 上传 server 目录
        print("  上传 server/ 目录...")
        upload_directory(sftp, "server", "/opt/vpn-proxy-client/server")
        
        # 上传 vpnproxy 目录
        print("  上传 vpnproxy/ 目录...")
        upload_directory(sftp, "vpnproxy", "/opt/vpn-proxy-client/vpnproxy")
        
        sftp.close()
        
        # 安装依赖（使用 --break-system-packages）
        print("\n3. 安装 Python 依赖...")
        deps_cmd = "cd /opt/vpn-proxy-client && pip3 install --break-system-packages -r server/requirements.txt"
        stdin, stdout, stderr = client.exec_command(deps_cmd, timeout=180)
        
        # 等待安装完成
        time.sleep(10)
        
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if "Successfully installed" in output or "already satisfied" in output:
            print("  依赖安装: 成功")
        elif error:
            print(f"  依赖安装警告: {error[:200]}")
        
        return True
        
    except Exception as e:
        print(f"部署错误: {e}")
        return False
    finally:
        if client:
            client.close()

def start_and_test_server():
    """启动并测试服务器"""
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
        print("停止现有进程...")
        client.exec_command("pkill -f 'python.*run.py'", timeout=30)
        time.sleep(3)
        
        # 启动服务器
        print("启动服务器...")
        start_cmd = """
        cd /opt/vpn-proxy-client
        nohup python3 -u server/run.py > /var/log/vpn-server.log 2>&1 &
        SERVER_PID=$!
        echo $SERVER_PID > /tmp/vpn-server.pid
        echo "服务器PID: $SERVER_PID"
        sleep 5
        """
        
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=30)
        output = stdout.read().decode().strip()
        if output:
            print(f"  启动输出: {output}")
        
        time.sleep(8)  # 给服务器更多时间启动
        
        # 检查状态
        print("\n检查服务器状态...")
        checks = []
        
        # 检查进程
        stdin, stdout, stderr = client.exec_command("ps aux | grep 'run.py' | grep -v grep", timeout=30)
        process_check = stdout.read().decode().strip()
        checks.append(("进程运行", bool(process_check)))
        if process_check:
            print(f"  进程: 运行中 (PID: {process_check.split()[1]})")
        
        # 检查端口
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18443 '", timeout=30)
        port_check = stdout.read().decode().strip()
        checks.append(("端口监听", bool(port_check)))
        if port_check:
            print(f"  端口: 监听中 {port_check}")
        
        # 检查日志
        stdin, stdout, stderr = client.exec_command("tail -30 /var/log/vpn-server.log 2>/dev/null || echo '日志文件正在生成...'", timeout=30)
        log_check = stdout.read().decode().strip()
        checks.append(("日志生成", "Traceback" not in log_check and "Error" not in log_check))
        print(f"  日志最后30行:\n{log_check}")
        
        # 检查证书
        stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/server/data/certs/ 2>/dev/null", timeout=30)
        cert_check = stdout.read().decode().strip()
        checks.append(("证书生成", "server.crt" in cert_check))
        if cert_check:
            print(f"  证书文件:\n{cert_check}")
        
        # 测试连接
        print("\n测试服务器连接...")
        test_script = """
import socket
import ssl
import sys

server = "localhost"
port = 18443

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((server, port))
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    ssl_sock = context.wrap_socket(sock, server_hostname=server)
    print("连接测试: 成功")
    ssl_sock.close()
    
except Exception as e:
    print(f"连接测试失败: {e}")
    sys.exit(1)
        """
        
        stdin, stdout, stderr = client.exec_command(f'python3 -c "{test_script}"', timeout=30)
        test_result = stdout.read().decode().strip()
        checks.append(("本地连接测试", "成功" in test_result))
        print(f"  连接测试: {test_result}")
        
        # 汇总结果
        print("\n" + "="*60)
        print("部署结果汇总:")
        for check_name, check_result in checks:
            status = "✅ 通过" if check_result else "❌ 失败"
            print(f"  {check_name}: {status}")
        
        all_passed = all(result for _, result in checks)
        return all_passed
        
    except Exception as e:
        print(f"测试错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始完整部署 VPN 服务器...")
    
    # 部署文件
    if deploy_complete():
        print("\n文件部署完成!")
        
        # 启动并测试
        if start_and_test_server():
            print("\n" + "="*60)
            print("🎉 SUCCESS: VPN 服务器部署并启动成功!")
            print("="*60)
            print("服务器信息:")
            print("  地址: 104.244.90.202:18443")
            print("  默认账号: demo / demo123")
            print("  日志: /var/log/vpn-server.log")
            print("  证书目录: /opt/vpn-proxy-client/server/data/certs/")
            print("="*60)
            print("\n下一步:")
            print("1. 下载证书: scp root@104.244.90.202:/opt/vpn-proxy-client/server/data/certs/server.crt .")
            print("2. 更新 APK 中的证书")
            print("3. 重新构建 APK 并测试")
        else:
            print("\n❌ ERROR: 服务器启动或测试失败")
    else:
        print("\n❌ ERROR: 文件部署失败")