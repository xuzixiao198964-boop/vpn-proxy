#!/usr/bin/env python3
"""
部署并启动 VPN 服务器
"""
import paramiko
import os
import time

def deploy_server_files():
    """部署服务器文件"""
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 部署 VPN 服务器文件 ===")
        
        # 1. 创建目录
        print("\n1. 创建服务器目录...")
        mkdir_cmds = [
            "mkdir -p /opt/vpn-proxy-client",
            "mkdir -p /opt/vpn-proxy-client/server",
            "mkdir -p /opt/vpn-proxy-client/vpnproxy",
            "mkdir -p /opt/vpn-proxy-client/server/data/certs"
        ]
        
        for cmd in mkdir_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        
        # 2. 上传服务器文件
        print("\n2. 上传服务器文件...")
        sftp = client.open_sftp()
        
        # 上传 server 目录文件
        server_files = [
            ("server/run.py", "/opt/vpn-proxy-client/server/run.py"),
            ("server/requirements.txt", "/opt/vpn-proxy-client/server/requirements.txt"),
            ("server/__init__.py", "/opt/vpn-proxy-client/server/__init__.py")
        ]
        
        for local, remote in server_files:
            if os.path.exists(local):
                sftp.put(local, remote)
                print(f"  上传: {local} -> {remote}")
        
        # 上传 vpnproxy 目录文件
        vpnproxy_files = [
            ("vpnproxy/__init__.py", "/opt/vpn-proxy-client/vpnproxy/__init__.py"),
            ("vpnproxy/client.py", "/opt/vpn-proxy-client/vpnproxy/client.py"),
            ("vpnproxy/protocol.py", "/opt/vpn-proxy-client/vpnproxy/protocol.py"),
            ("vpnproxy/server.py", "/opt/vpn-proxy-client/vpnproxy/server.py"),
            ("vpnproxy/socks5.py", "/opt/vpn-proxy-client/vpnproxy/socks5.py"),
            ("vpnproxy/tunnel.py", "/opt/vpn-proxy-client/vpnproxy/tunnel.py")
        ]
        
        for local, remote in vpnproxy_files:
            if os.path.exists(local):
                sftp.put(local, remote)
                print(f"  上传: {local} -> {remote}")
        
        sftp.close()
        
        # 3. 安装依赖
        print("\n3. 安装依赖...")
        deps_cmd = "cd /opt/vpn-proxy-client && pip3 install -r server/requirements.txt"
        stdin, stdout, stderr = client.exec_command(deps_cmd, timeout=120)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"  输出: {output[-200:] if len(output) > 200 else output}")
        if error and "already satisfied" not in error:
            print(f"  错误: {error[-200:] if len(error) > 200 else error}")
        
        return True
        
    except Exception as e:
        print(f"部署错误: {e}")
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
        print("停止现有进程...")
        client.exec_command("pkill -f 'python.*run.py'", timeout=30)
        time.sleep(2)
        
        # 启动服务器
        print("启动服务器...")
        start_cmd = """
        cd /opt/vpn-proxy-client
        nohup python3 -u server/run.py > /var/log/vpn-server.log 2>&1 &
        echo $! > /tmp/vpn-server.pid
        sleep 3
        """
        
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=30)
        time.sleep(5)
        
        # 检查状态
        print("检查启动状态...")
        status_cmds = [
            "ps aux | grep 'run.py' | grep -v grep",
            "ss -tlnp | grep ':18443 '",
            "tail -20 /var/log/vpn-server.log 2>/dev/null || echo '等待日志生成...'"
        ]
        
        results = []
        for cmd in status_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            results.append(output)
            if output:
                print(f"  {cmd}: {output}")
        
        # 检查端口
        print("\n测试端口连接...")
        test_cmd = "timeout 3 bash -c 'echo > /dev/tcp/localhost/18443' 2>&1 && echo '端口可访问' || echo '端口不可访问'"
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        port_test = stdout.read().decode().strip()
        print(f"  端口测试: {port_test}")
        
        # 检查证书
        print("\n检查证书生成...")
        cert_cmd = "ls -la /opt/vpn-proxy-client/server/data/certs/ 2>/dev/null && echo '证书已生成' || echo '证书未生成'"
        stdin, stdout, stderr = client.exec_command(cert_cmd, timeout=30)
        cert_status = stdout.read().decode().strip()
        print(f"  证书状态: {cert_status}")
        
        return all(results[0:2])  # 进程和端口都正常
        
    except Exception as e:
        print(f"启动错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始部署和启动 VPN 服务器...")
    
    # 部署文件
    if deploy_server_files():
        print("\n文件部署完成!")
        
        # 启动服务器
        if start_vpn_server():
            print("\n" + "="*60)
            print("SUCCESS: VPN 服务器已启动!")
            print("="*60)
            print("服务器信息:")
            print("  地址: 104.244.90.202:18443")
            print("  默认账号: demo / demo123")
            print("  日志: /var/log/vpn-server.log")
            print("  证书目录: /opt/vpn-proxy-client/server/data/certs/")
            print("="*60)
            print("\n下一步:")
            print("1. 下载证书: scp root@104.244.90.202:/opt/vpn-proxy-client/server/data/certs/server.crt .")
            print("2. 测试连接")
        else:
            print("\nERROR: VPN 服务器启动失败")
    else:
        print("\nERROR: 文件部署失败")