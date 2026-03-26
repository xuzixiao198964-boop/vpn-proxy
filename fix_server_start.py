#!/usr/bin/env python3
"""
修复服务器启动问题
"""
import paramiko
import time

def fix_server_issues():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 修复服务器问题 ===")
        
        # 1. 检查 Python 路径
        print("\n1. 检查 Python 环境...")
        check_cmds = [
            "python3 --version",
            "cd /opt/vpn-proxy-client && python3 -c 'import sys; print(sys.path)'",
            "cd /opt/vpn-proxy-client && ls -la vpnproxy/"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            if output:
                print(f"  {cmd}: {output[:200]}")
        
        # 2. 创建正确的启动脚本
        print("\n2. 创建正确的启动脚本...")
        startup_script = """#!/bin/bash
cd /opt/vpn-proxy-client

# 添加当前目录到 Python 路径
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH

# 停止现有进程
pkill -f "python.*run.py" 2>/dev/null
sleep 2

# 启动服务器
nohup python3 -u server/run.py > /var/log/vpn-server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/vpn-server.pid
echo "VPN服务器已启动，PID: $SERVER_PID"

# 等待启动
sleep 5

# 检查状态
if ps -p $SERVER_PID > /dev/null; then
    echo "服务器进程运行正常"
else
    echo "服务器进程可能已退出，检查日志: /var/log/vpn-server.log"
    exit 1
fi

# 检查端口
if ss -tlnp | grep -q ':18443 '; then
    echo "端口 18443 监听正常"
else
    echo "端口 18443 未监听"
    exit 1
fi

echo "VPN服务器启动完成"
"""
        
        # 上传启动脚本
        stdin, stdout, stderr = client.exec_command("cat > /opt/vpn-proxy-client/start_vpn.sh", timeout=30)
        stdin.write(startup_script)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        client.exec_command("chmod +x /opt/vpn-proxy-client/start_vpn.sh", timeout=30)
        print("  启动脚本创建完成")
        
        # 3. 测试模块导入
        print("\n3. 测试模块导入...")
        test_import = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH
python3 -c "
try:
    from vpnproxy.auth_store import AuthStore
    print('SUCCESS: 模块导入成功')
    print('AuthStore类:', AuthStore)
except ImportError as e:
    print('ERROR: 模块导入失败:', e)
    import sys
    print('Python路径:', sys.path)
"
"""
        
        stdin, stdout, stderr = client.exec_command(test_import, timeout=30)
        import_result = stdout.read().decode().strip()
        print(f"  导入测试: {import_result}")
        
        # 4. 启动服务器
        print("\n4. 启动 VPN 服务器...")
        stdin, stdout, stderr = client.exec_command("cd /opt/vpn-proxy-client && ./start_vpn.sh", timeout=60)
        start_output = stdout.read().decode().strip()
        start_error = stderr.read().decode().strip()
        
        print(f"  启动输出:\n{start_output}")
        if start_error:
            print(f"  启动错误: {start_error}")
        
        # 5. 检查最终状态
        print("\n5. 检查最终状态...")
        final_checks = [
            ("进程状态", "ps aux | grep 'run.py' | grep -v grep"),
            ("端口监听", "ss -tlnp | grep ':18443 '"),
            ("服务器日志", "tail -10 /var/log/vpn-server.log"),
            ("证书生成", "ls -la /opt/vpn-proxy-client/server/data/certs/")
        ]
        
        all_ok = True
        for check_name, cmd in final_checks:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            ok = bool(output) and "Traceback" not in output and "Error" not in output
            
            status = "OK" if ok else "FAILED"
            print(f"  {check_name}: {status}")
            if output and len(output) < 100:
                print(f"    详情: {output}")
            
            if not ok:
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"修复错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始修复服务器问题...")
    if fix_server_issues():
        print("\n" + "="*60)
        print("SUCCESS: 服务器问题修复完成!")
        print("="*60)
        print("VPN 服务器信息:")
        print("  地址: 104.244.90.202:18443")
        print("  启动脚本: /opt/vpn-proxy-client/start_vpn.sh")
        print("  日志文件: /var/log/vpn-server.log")
        print("="*60)
    else:
        print("\nERROR: 服务器问题修复失败")