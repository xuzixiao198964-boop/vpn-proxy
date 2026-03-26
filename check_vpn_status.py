#!/usr/bin/env python3
"""
检查 VPN 服务器状态和连接问题
"""
import paramiko
import time

def check_vpn_server():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== VPN 服务器状态检查 ===")
        
        # 1. 检查 VPN 服务进程
        print("\n1. 检查 VPN 服务进程:")
        cmds = [
            "ps aux | grep 'run.py' | grep -v grep",
            "ss -tlnp | grep ':18443 '",
            "netstat -tlnp | grep ':18443'"
        ]
        
        for cmd in cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {cmd}: {output}")
        
        # 2. 检查服务日志
        print("\n2. 检查服务日志 (最后20行):")
        log_cmds = [
            "tail -20 /opt/vpn-proxy-client/server.log 2>/dev/null || echo '无日志文件'",
            "journalctl -u vpn-proxy --no-pager -n 20 2>/dev/null || echo '无systemd服务'"
        ]
        
        for cmd in log_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {output}")
        
        # 3. 测试服务器网络连通性
        print("\n3. 测试服务器网络连通性:")
        test_cmds = [
            "curl -s --connect-timeout 5 https://facebook.com | grep -i facebook || echo '无法访问Facebook'",
            "curl -s --connect-timeout 5 https://google.com | grep -i google || echo '无法访问Google'",
            "ping -c 2 8.8.8.8 2>/dev/null | grep 'packets transmitted' || echo '无法ping通'"
        ]
        
        for cmd in test_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {output}")
        
        # 4. 检查防火墙规则
        print("\n4. 检查防火墙规则:")
        firewall_cmds = [
            "iptables -L -n 2>/dev/null | head -20 || echo '无iptables或需要sudo'",
            "ufw status 2>/dev/null || echo '无ufw'"
        ]
        
        for cmd in firewall_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {output}")
        
        # 5. 检查用户数据库
        print("\n5. 检查用户数据库:")
        db_cmd = "ls -la /opt/vpn-proxy-client/server/data/ 2>/dev/null || echo '数据目录不存在'"
        stdin, stdout, stderr = client.exec_command(db_cmd, timeout=30)
        output = stdout.read().decode().strip()
        if output:
            print(f"  数据目录: {output}")
        
        # 6. 检查证书
        print("\n6. 检查证书文件:")
        cert_cmd = "ls -la /opt/vpn-proxy-client/server/data/certs/ 2>/dev/null || echo '证书目录不存在'"
        stdin, stdout, stderr = client.exec_command(cert_cmd, timeout=30)
        output = stdout.read().decode().strip()
        if output:
            print(f"  证书文件: {output}")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

def test_client_connection():
    """测试客户端连接"""
    print("\n=== 本地客户端连接测试 ===")
    
    import socket
    import ssl
    
    server = "104.244.90.202"
    port = 18443
    
    try:
        # 测试 TCP 连接
        print(f"测试连接到 {server}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((server, port))
        print("  TCP 连接: 成功")
        
        # 测试 SSL/TLS
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        ssl_sock = context.wrap_socket(sock, server_hostname=server)
        print("  SSL/TLS 握手: 成功")
        
        # 获取证书信息
        cert = ssl_sock.getpeercert()
        if cert:
            print(f"  服务器证书: {cert.get('subject', '未知')}")
        
        ssl_sock.close()
        return True
        
    except socket.timeout:
        print("  TCP 连接: 超时")
        return False
    except ConnectionRefusedError:
        print("  TCP 连接: 被拒绝")
        return False
    except ssl.SSLError as e:
        print(f"  SSL/TLS 错误: {e}")
        return False
    except Exception as e:
        print(f"  连接错误: {e}")
        return False

if __name__ == "__main__":
    print("开始诊断 VPN 连接问题...")
    
    # 检查服务器状态
    server_ok = check_vpn_server()
    
    # 测试客户端连接
    client_ok = test_client_connection()
    
    print("\n" + "="*60)
    print("诊断结果:")
    print(f"  服务器状态: {'正常' if server_ok else '有问题'}")
    print(f"  客户端连接: {'正常' if client_ok else '失败'}")
    
    if not client_ok:
        print("\n建议:")
        print("1. 检查服务器防火墙是否允许 18443 端口")
        print("2. 检查 VPN 服务是否正在运行")
        print("3. 检查服务器网络连接")
        print("4. 查看服务器日志获取更多信息")
    
    print("="*60)