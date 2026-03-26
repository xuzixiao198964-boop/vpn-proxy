#!/usr/bin/env python3
"""
清理缓存并重启服务器
"""
import paramiko
import time

def clean_and_restart():
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        
        print("=== 清理缓存并重启 ===")
        
        # 1. 清理 Python 缓存
        print("1. 清理 Python 缓存...")
        clean_cmds = [
            "find /opt/vpn-proxy-client -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true",
            "find /opt/vpn-proxy-client -name '*.pyc' -delete 2>/dev/null || true",
            "find /opt/vpn-proxy-client -name '*.pyo' -delete 2>/dev/null || true"
        ]
        
        for cmd in clean_cmds:
            client.exec_command(cmd, timeout=30)
        
        # 2. 停止所有相关进程
        print("2. 停止所有进程...")
        client.exec_command("pkill -f 'python.*run.py'", timeout=30)
        client.exec_command("pkill -f 'python3.*run.py'", timeout=30)
        time.sleep(3)
        
        # 3. 验证文件存在
        print("3. 验证文件...")
        check_cmds = [
            "ls -la /opt/vpn-proxy-client/vpnproxy/*.py",
            "wc -l /opt/vpn-proxy-client/vpnproxy/*.py"
        ]
        
        for cmd in check_cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            output = stdout.read().decode().strip()
            print(f"  {cmd}: {output[:200]}")
        
        # 4. 直接运行测试
        print("4. 直接运行测试...")
        direct_test = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH

# 直接运行服务器，捕获输出
python3 server/run.py 2>&1 | head -20
"""
        
        stdin, stdout, stderr = client.exec_command(direct_test, timeout=30)
        direct_output = stdout.read().decode().strip()
        print(f"直接运行输出:\n{direct_output}")
        
        if "Traceback" in direct_output or "Error" in direct_output:
            print("直接运行失败，检查具体错误...")
            
            # 运行更详细的测试
            debug_test = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH
python3 -c "
import sys
print('Python路径:', sys.path)
print()
try:
    import vpnproxy
    print('vpnproxy 模块导入成功')
    print('模块内容:', dir(vpnproxy))
except Exception as e:
    print('vpnproxy 导入失败:', e)
print()
try:
    from vpnproxy import auth_store
    print('auth_store 导入成功')
    print('auth_store 内容:', dir(auth_store))
except Exception as e:
    print('auth_store 导入失败:', e)
"
"""
            
            stdin, stdout, stderr = client.exec_command(debug_test, timeout=30)
            debug_output = stdout.read().decode().strip()
            print(f"调试信息:\n{debug_output}")
            
            return False
        
        # 5. 在后台启动
        print("5. 在后台启动服务器...")
        background_start = """
cd /opt/vpn-proxy-client
export PYTHONPATH=/opt/vpn-proxy-client:$PYTHONPATH

# 清理旧日志
> /var/log/vpn-server.log

# 启动
nohup python3 -u server/run.py >> /var/log/vpn-server.log 2>&1 &
SERVER_PID=$!
echo "服务器PID: $SERVER_PID"
echo $SERVER_PID > /tmp/vpn-server.pid

# 等待
sleep 10

# 检查
echo "检查进程:"
ps -p $SERVER_PID >/dev/null && echo "进程存活" || echo "进程死亡"

echo "检查端口:"
ss -tlnp | grep ':18443 ' || echo "端口未监听"

echo "检查日志最后5行:"
tail -5 /var/log/vpn-server.log
"""
        
        stdin, stdout, stderr = client.exec_command(background_start, timeout=60)
        start_output = stdout.read().decode().strip()
        print(f"启动结果:\n{start_output}")
        
        # 6. 最终检查
        print("6. 最终检查...")
        stdin, stdout, stderr = client.exec_command("ss -tlnp | grep ':18443 '", timeout=30)
        final_check = stdout.read().decode().strip()
        
        if final_check:
            print(f"SUCCESS: VPN 服务器运行正常!")
            print(f"端口状态: {final_check}")
            
            # 获取证书
            stdin, stdout, stderr = client.exec_command("ls -la /opt/vpn-proxy-client/server/data/certs/", timeout=30)
            certs = stdout.read().decode().strip()
            print(f"证书文件:\n{certs}")
            
            return True
        else:
            print("ERROR: 服务器未运行")
            
            # 查看详细日志
            stdin, stdout, stderr = client.exec_command("tail -20 /var/log/vpn-server.log", timeout=30)
            detailed_log = stdout.read().decode().strip()
            print(f"详细日志:\n{detailed_log}")
            
            return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("开始清理和重启 VPN 服务器...")
    if clean_and_restart():
        print("\n" + "="*60)
        print("SUCCESS: VPN 服务器已启动!")
        print("="*60)
        print("服务器信息:")
        print("  地址: 104.244.90.202:18443")
        print("  默认账号: demo / demo123")
        print("="*60)
    else:
        print("\nERROR: 服务器启动失败")