#!/usr/bin/env python3
"""
SSH 自动化脚本，用于连接服务器执行命令
"""
import paramiko
import sys
import time

def ssh_execute(host, port, username, password, commands):
    """通过 SSH 执行命令"""
    client = None
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"连接到 {username}@{host}:{port}...")
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        print("连接成功!")
        
        results = []
        for cmd in commands:
            print(f"\n执行命令: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            
            # 读取输出
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()
            
            if output:
                print(f"输出:\n{output}")
                results.append((cmd, output, None))
            if error:
                print(f"错误:\n{error}")
                results.append((cmd, None, error))
        
        return results
        
    except Exception as e:
        print(f"SSH 连接错误: {e}")
        return None
    finally:
        if client:
            client.close()

def main():
    # 服务器信息
    host = "104.244.90.202"
    port = 22
    username = "root"
    password = "v9wSxMxg92dp"
    
    # 要执行的命令
    commands = [
        # 1. 检查 80 端口服务
        "ss -tlnp | grep ':80 '",
        # 2. 检查 ai-img-platform 服务
        "systemctl list-units --type=service --state=running | grep -i img",
        # 3. 检查 Docker 容器
        "docker ps | grep -i img",
        # 4. 检查进程
        "ps aux | grep -i img | grep -v grep"
    ]
    
    print("=== 开始执行服务器操作 ===")
    results = ssh_execute(host, port, username, password, commands)
    
    if results:
        print("\n=== 执行结果汇总 ===")
        for cmd, output, error in results:
            print(f"\n命令: {cmd}")
            if output:
                print(f"输出: {output}")
            if error:
                print(f"错误: {error}")
    else:
        print("执行失败")

if __name__ == "__main__":
    main()