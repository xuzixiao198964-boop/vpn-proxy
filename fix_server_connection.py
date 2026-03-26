#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务器 VPN 服务连接问题
"""
import paramiko
import time

def fix_server():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    print("=== 修复服务器 VPN 服务 ===")
    print(f"服务器: {host}")
    print(f"端口: {port}")
    print(f"用户名: {username}")
    
    client = None
    try:
        # 连接服务器
        print("连接服务器...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("连接成功!")
        
        # 1. 检查当前端口状态
        print("\n1. 检查 18443 端口状态:")
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18443'", timeout=30)
        port_status = stdout.read().decode().strip()
        if port_status:
            print(f"   端口 18443 正在监听: {port_status}")
        else:
            print("   端口 18443 未监听")
        
        # 2. 检查 VPN 服务目录
        print("\n2. 检查 VPN 服务文件:")
        stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/", timeout=30)
        files = stdout.read().decode().strip()
        print(f"   {files}")
        
        # 3. 检查 Python 模块问题
        print("\n3. 检查 Python 模块导入问题:")
        stdin, stdout, stderr = client.exec_command("cd /opt/vpn-proxy-client && python3 -c 'import sys; sys.path.insert(0, \".\"); import vpnproxy.auth_store' 2>&1", timeout=30)
        import_result = stdout.read().decode().strip()
        if "ModuleNotFoundError" in import_result:
            print("   发现模块导入错误")
            print(f"   错误: {import_result}")
            
            # 4. 修复模块导入
            print("\n4. 修复模块导入:")
            
            # 检查目录结构
            stdin, stdout, stderr = client.exec_command("find /opt/vpn-proxy-client -name '*.py' -type f | head -20", timeout=30)
            py_files = stdout.read().decode().strip()
            print(f"   Python 文件:\n{py_files}")
            
            # 检查 vpnproxy 目录
            stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/vpnproxy/ 2>/dev/null || echo 'vpnproxy目录不存在'", timeout=30)
            vpnproxy_dir = stdout.read().decode().strip()
            print(f"   vpnproxy目录:\n{vpnproxy_dir}")
            
            # 创建 __init__.py 文件
            print("\n5. 创建缺失的 __init__.py 文件:")
            init_cmds = [
                "touch /opt/vpn-proxy-client/vpnproxy/__init__.py",
                "touch /opt/vpn-proxy-client/vpnproxy/auth_store/__init__.py 2>/dev/null || mkdir -p /opt/vpn-proxy-client/vpnproxy/auth_store && touch /opt/vpn-proxy-client/vpnproxy/auth_store/__init__.py"
            ]
            
            for cmd in init_cmds:
                stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
                print(f"   执行: {cmd}")
        
        # 5. 尝试启动 VPN 服务
        print("\n6. 尝试启动 VPN 服务:")
        start_cmd = "cd /opt/vpn-proxy-client && export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH && python3 server/run.py 2>&1 &"
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=30)
        print(f"   启动命令: {start_cmd}")
        
        # 等待一下
        time.sleep(2)
        
        # 6. 检查是否启动成功
        print("\n7. 检查服务状态:")
        check_cmds = [
            "ps aux | grep 'python3 server/run.py' | grep -v grep",
            "ss -tlnp | grep ':18443'",
            "netstat -tlnp | grep ':18443' 2>/dev/null || echo '使用ss命令'"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            result = stdout.read().decode().strip()
            if result:
                print(f"   {cmd}: {result}")
        
        # 7. 测试端口连接
        print("\n8. 测试端口连接:")
        test_cmd = "timeout 5 bash -c 'echo > /dev/tcp/127.0.0.1/18443' && echo '端口可连接' || echo '端口不可连接'"
        stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
        test_result = stdout.read().decode().strip()
        print(f"   本地连接测试: {test_result}")
        
        print("\n" + "="*60)
        print("修复完成!")
        print("="*60)
        print("如果 VPN 服务启动成功，APK 应该可以连接。")
        print("如果仍有问题，请检查服务器日志:")
        print("  cd /opt/vpn-proxy-client")
        print("  tail -f server.log 2>/dev/null || python3 server/run.py")
        print("="*60)
        
    except Exception as e:
        print(f"修复失败: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    fix_server()