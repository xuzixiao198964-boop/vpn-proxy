#!/usr/bin/env python3
import paramiko

def check_meis():
    host = '104.244.90.202'
    username = 'root'
    password = 'v9wSxMxg92dp'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, 22, username, password, timeout=10)
        
        print('检查 multi-end-intelligent-service 项目...')
        
        # 1. 检查项目目录是否存在
        cmd1 = 'ls -la /root/ | grep -i multi'
        stdin, stdout, stderr = client.exec_command(cmd1, timeout=5)
        print('项目目录:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 2. 检查是否有后端服务
        cmd2 = 'find /root -name "*.py" -o -name "requirements.txt" -o -name "package.json" 2>/dev/null | head -20'
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=5)
        print('相关文件:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 3. 检查是否有安装脚本
        cmd3 = 'find /root -name "install.sh" -o -name "setup.sh" -o -name "deploy.sh" 2>/dev/null'
        stdin, stdout, stderr = client.exec_command(cmd3, timeout=5)
        print('安装脚本:')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # 4. 检查 8001 端口是否被占用
        cmd4 = 'lsof -i :8001'
        stdin, stdout, stderr = client.exec_command(cmd4, timeout=5)
        output = stdout.read().decode('utf-8', errors='ignore')
        print('8001 端口状态:')
        if output:
            print(output)
        else:
            print('端口 8001 未被占用')
        
    except Exception as e:
        print(f'错误: {e}')
        
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == '__main__':
    check_meis()