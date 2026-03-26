#!/usr/bin/env python3
import paramiko

def check_server():
    host = '104.244.90.202'
    username = 'root'
    password = 'v9wSxMxg92dp'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, 22, username, password, timeout=10)
        
        print('检查服务器状态...')
        
        # 1. 检查 meis-server 服务状态
        cmd1 = 'systemctl status meis-server --no-pager -l'
        stdin, stdout, stderr = client.exec_command(cmd1, timeout=5)
        status_output = stdout.read().decode('utf-8', errors='ignore')
        error_output = stderr.read().decode('utf-8', errors='ignore')
        
        print('meis-server 服务状态:')
        print(status_output)
        if error_output:
            print('错误:', error_output)
        
        # 2. 检查端口监听
        cmd2 = 'netstat -tlnp | grep -E ":(8000|8001|8080|18080)"'
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=5)
        print('端口监听状态:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 3. 检查进程
        cmd3 = 'ps aux | grep -E "node|npm|python" | grep -v grep'
        stdin, stdout, stderr = client.exec_command(cmd3, timeout=5)
        print('相关进程:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 4. 检查日志
        cmd4 = 'journalctl -u meis-server -n 20 --no-pager'
        stdin, stdout, stderr = client.exec_command(cmd4, timeout=5)
        print('服务日志:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
    except Exception as e:
        print(f'错误: {e}')
        
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == '__main__':
    check_server()