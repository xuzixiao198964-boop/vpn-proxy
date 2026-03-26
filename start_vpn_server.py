#!/usr/bin/env python3
"""
启动 VPN 服务器
"""
import paramiko
import time

def start_vpn_server():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 启动 VPN 服务器 ===")
        
        # 1. 检查项目目录
        print("\n1. 检查项目目录...")
        check_cmds = [
            "ls -la /opt/vpn-proxy-client/",
            "ls -la /opt/vpn-proxy-client/server/",
            "ls -la /opt/vpn-proxy-client/vpnproxy/"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {output[:200]}...")
        
        # 2. 安装依赖
        print("\n2. 安装 Python 依赖...")
        deps_cmd = "cd /opt/vpn-proxy-client && pip3 install -r server/requirements.txt 2>&1 | tail -5"
        stdin, stdout, stderr = client.exec_command(deps_cmd, timeout=60)
        output = stdout.read().decode().strip()
        if output:
            print(f"  依赖安装: {output}")
        
        # 3. 启动 VPN 服务器
        print("\n3. 启动 VPN 服务器...")
        
        # 先停止可能存在的进程
        client.exec_command("pkill -f 'python.*run.py'", timeout=30)
        time.sleep(2)
        
        # 在后台启动服务器
        start_cmd = """
        cd /opt/vpn-proxy-client
        nohup python3 server/run.py > /var/log/vpn-server.log 2>&1 &
        echo $! > /tmp/vpn-server.pid
        """
        
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=30)
        time.sleep(5)  # 给服务器启动时间
        
        # 4. 检查是否启动成功
        print("\n4. 检查启动状态...")
        status_cmds = [
            "ps aux | grep 'run.py' | grep -v grep",
            "ss -tlnp | grep ':18443 '",
            "tail -10 /var/log/vpn-server.log 2>/dev/null || echo '日志文件不存在'"
        ]
        
        for cmd in status_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {cmd}: {output}")
        
        # 5. 检查证书生成
        print("\n5. 检查证书生成...")
        cert_cmd = "ls -la /opt/vpn-proxy-client/server/data/certs/ 2>/dev/null || echo '正在生成证书...'"
        stdin, stdout, stderr = client.exec_command(cert_cmd, timeout=30)
        output = stdout.read().decode().strip()
        if output:
            print(f"  证书: {output}")
        
        # 6. 测试服务器监听
        print("\n6. 测试服务器监听...")
        test_cmd = "timeout 5 bash -c 'echo > /dev/tcp/localhost/18443' && echo '端口可访问' || echo '端口不可访问'"
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        output = stdout.read().decode().strip()
        print(f"  端口测试: {output}")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始启动 VPN 服务器...")
    if start_vpn_server():
        print("\n" + "="*60)
        print("SUCCESS: VPN 服务器启动完成!")
        print("="*60)
        print("服务器信息:")
        print("  地址: 104.244.90.202:18443")
        print("  默认账号: demo / demo123")
        print("  日志文件: /var/log/vpn-server.log")
        print("="*60)
    else:
        print("\nERROR: VPN 服务器启动失败")