#!/usr/bin/env python3
import paramiko
import sys

def setup_nginx():
    host = '104.244.90.202'
    username = 'root'
    password = 'v9wSxMxg92dp'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, 22, username, password, timeout=10)
        
        print('🚀 配置 Nginx 代理...')
        
        # 1. 创建 Nginx 配置文件
        nginx_config = '''server {
    listen 11000;
    server_name _;
    root /opt/downloads;
    
    location / {
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # 允许大文件下载
        client_max_body_size 100M;
        
        # 设置正确的 MIME 类型
        types {
            application/vnd.android.package-archive apk;
            text/plain txt;
        }
        
        # 添加下载头
        add_header Content-Disposition 'attachment; filename="$request_filename"' always;
    }
    
    # 防止访问隐藏文件
    location ~ /\\. {
        deny all;
    }
}'''
        
        # 保存配置文件
        cmd1 = f'echo "{nginx_config}" > /etc/nginx/sites-available/downloads'
        stdin, stdout, stderr = client.exec_command(cmd1, timeout=5)
        print('📁 创建配置文件...')
        
        # 2. 启用站点
        cmd2 = 'ln -sf /etc/nginx/sites-available/downloads /etc/nginx/sites-enabled/ && nginx -t'
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=5)
        print('🔗 启用站点...')
        output = stdout.read().decode() + stderr.read().decode()
        print(output)
        
        # 3. 重启 Nginx
        cmd3 = 'systemctl restart nginx'
        stdin, stdout, stderr = client.exec_command(cmd3, timeout=5)
        print('🔄 重启 Nginx...')
        
        # 4. 检查状态
        cmd4 = 'systemctl status nginx --no-pager -l'
        stdin, stdout, stderr = client.exec_command(cmd4, timeout=5)
        print('📊 Nginx 状态:')
        print(stdout.read().decode())
        
        # 5. 检查端口监听
        cmd5 = 'netstat -tlnp | grep :11000'
        stdin, stdout, stderr = client.exec_command(cmd5, timeout=5)
        print('🔍 端口监听状态:')
        print(stdout.read().decode())
        
        # 6. 确保 APK 文件完整
        cmd6 = 'ls -lh /opt/downloads/'
        stdin, stdout, stderr = client.exec_command(cmd6, timeout=5)
        print('📁 文件列表:')
        print(stdout.read().decode())
        
        print('')
        print('✅ Nginx 配置完成！')
        print('')
        print('🎯 下载链接:')
        print('http://104.244.90.202:11000/VpnProxyClient-debug.apk')
        print('')
        print('📄 测试链接:')
        print('http://104.244.90.202:11000/test.txt')
        
    except Exception as e:
        print(f'❌ 错误: {e}')
        
        # 备用方案：直接启动 Python 服务器
        print('')
        print('🔄 尝试备用方案：启动 Python HTTP 服务器...')
        try:
            cmd_fallback = 'cd /opt/downloads && nohup python3 -m http.server 11000 --bind 0.0.0.0 > /tmp/nginx_fallback.log 2>&1 &'
            stdin, stdout, stderr = client.exec_command(cmd_fallback, timeout=5)
            print('✅ Python 服务器已启动')
            print('')
            print('🎯 下载链接:')
            print('http://104.244.90.202:11000/VpnProxyClient-debug.apk')
        except Exception as e2:
            print(f'❌ 备用方案也失败: {e2}')
            
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == '__main__':
    setup_nginx()