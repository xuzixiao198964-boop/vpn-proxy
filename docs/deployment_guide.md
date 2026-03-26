# VPN 代理隧道 - 部署指南

## 概述

本文档提供 VPN 代理隧道项目的完整部署指南，包括服务端部署、客户端部署和运维管理。

## 1. 系统要求

### 1.1 服务端要求

#### 硬件要求
| 资源 | 最低要求 | 推荐配置 | 生产环境 |
|------|----------|----------|----------|
| CPU | 1 核 | 2 核 | 4 核 |
| 内存 | 512 MB | 2 GB | 4 GB |
| 存储 | 10 GB | 20 GB | 50 GB |
| 带宽 | 10 Mbps | 100 Mbps | 1 Gbps |

#### 软件要求
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **Python**: 3.8 或更高版本
- **OpenSSL**: 1.1.1 或更高版本
- **数据库**: SQLite 3（内置）或 PostgreSQL（可选）

#### 网络要求
- 公网 IP 地址
- 开放 TCP 端口: 18443（默认）
- 防火墙配置允许入站连接

### 1.2 客户端要求

#### Windows 客户端
- **操作系统**: Windows 10/11（64位）
- **Python**: 3.8 或更高版本
- **内存**: 至少 1 GB 可用内存
- **存储**: 至少 100 MB 可用空间

#### Android 客户端
- **系统版本**: Android 8.0（API 26）或更高
- **架构**: arm64-v8a, armeabi-v7a, x86_64, x86
- **权限**: VPN 权限、网络权限

## 2. 服务端部署

### 2.1 快速部署（一键脚本）

#### 2.1.1 使用部署脚本
```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/xuzixiao198964-boop/vpn-proxy/master/scripts/install_server_vps.sh

# 赋予执行权限
chmod +x install_server_vps.sh

# 执行部署
sudo ./install_server_vps.sh
```

#### 2.1.2 脚本执行过程
1. 更新系统软件包
2. 安装 Python 和依赖
3. 创建系统用户和目录
4. 配置防火墙
5. 设置系统服务
6. 启动 VPN 服务

### 2.2 手动部署

#### 2.2.1 环境准备
```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装基础工具
sudo apt install -y python3 python3-pip python3-venv git curl wget

# 安装 OpenSSL
sudo apt install -y openssl libssl-dev

# 创建专用用户
sudo useradd -r -m -s /bin/bash vpnproxy
sudo passwd -l vpnproxy
```

#### 2.2.2 项目部署
```bash
# 切换到专用用户
sudo su - vpnproxy

# 克隆项目代码
cd /opt
git clone https://github.com/xuzixiao198964-boop/vpn-proxy.git
cd vpn-proxy

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r server/requirements.txt
```

#### 2.2.3 证书生成
```bash
# 生成服务器证书（自动）
cd server
python3 -c "from cert_util import generate_self_signed_cert; generate_self_signed_cert()"

# 或者手动生成
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=vpn.example.com"
```

#### 2.2.4 服务配置
```bash
# 创建配置文件
cat > config.yaml << EOF
server:
  host: 0.0.0.0
  port: 18443
  cert_file: data/certs/server.crt
  key_file: data/certs/server.key
  
database:
  path: data/users.db
  
logging:
  level: INFO
  file: logs/server.log
  max_size: 10485760  # 10MB
  backup_count: 5
  
security:
  max_connections: 100
  rate_limit: 10  # 连接/秒
  session_timeout: 3600  # 1小时
EOF
```

#### 2.2.5 系统服务配置
```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/vpn-proxy.service << EOF
[Unit]
Description=VPN Proxy Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=vpnproxy
Group=vpnproxy
WorkingDirectory=/opt/vpn-proxy
Environment="PATH=/opt/vpn-proxy/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/vpn-proxy/venv/bin/python server/run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable vpn-proxy.service

# 启动服务
sudo systemctl start vpn-proxy.service

# 检查状态
sudo systemctl status vpn-proxy.service
```

### 2.3 防火墙配置

#### 2.3.1 UFW 配置
```bash
# 安装 UFW
sudo apt install -y ufw

# 配置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 开放 SSH 端口
sudo ufw allow 22/tcp

# 开放 VPN 端口
sudo ufw allow 18443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status verbose
```

#### 2.3.2 iptables 配置
```bash
# 允许 VPN 端口
sudo iptables -A INPUT -p tcp --dport 18443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -P INPUT DROP

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4
```

### 2.4 反向代理配置（可选）

#### 2.4.1 Nginx 配置
```bash
# 安装 Nginx
sudo apt install -y nginx

# 创建站点配置
sudo tee /etc/nginx/sites-available/vpn-proxy << EOF
server {
    listen 443 ssl http2;
    server_name vpn.example.com;
    
    ssl_certificate /opt/vpn-proxy/server/data/certs/server.crt;
    ssl_certificate_key /opt/vpn-proxy/server/data/certs/server.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass https://127.0.0.1:18443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/vpn-proxy /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

## 3. 客户端部署

### 3.1 Windows 客户端部署

#### 3.1.1 手动安装
```powershell
# 1. 安装 Python 3.8+
# 从 https://www.python.org/downloads/ 下载并安装

# 2. 克隆项目
git clone https://github.com/xuzixiao198964-boop/vpn-proxy.git
cd vpn-proxy

# 3. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 4. 安装依赖
pip install -r windows_client/requirements.txt

# 5. 运行客户端
python -m windows_client.app_gui
```

#### 3.1.2 创建快捷方式
```powershell
# 创建启动脚本
@echo off
cd /d "E:\work\vpn-proxy-client"
call venv\Scripts\activate.bat
python -m windows_client.app_gui
pause
```

#### 3.1.3 打包为可执行文件（可选）
```powershell
# 安装 PyInstaller
pip install pyinstaller

# 打包应用
pyinstaller --onefile --windowed --name "VPNProxyClient" windows_client/app_gui.py

# 输出在 dist/VPNProxyClient.exe
```

### 3.2 Android 客户端部署

#### 3.2.1 直接安装 APK
1. 从 `dist/` 目录获取最新的 APK 文件
2. 传输到 Android 设备
3. 在设备上启用"未知来源"安装
4. 安装 APK 文件

#### 3.2.2 从源代码构建
```bash
# 1. 安装 Android Studio 和 SDK
# 2. 配置环境变量
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# 3. 进入 Android 目录
cd android

# 4. 构建 APK
./gradlew assembleDebug

# 5. 生成的 APK 在:
# android/app/build/outputs/apk/debug/app-debug.apk
```

#### 3.2.3 发布到 Google Play
1. 生成签名密钥
2. 构建发布版本 APK
3. 在 Google Play Console 创建应用
4. 上传 APK 并填写应用信息
5. 提交审核

## 4. 配置管理

### 4.1 服务端配置

#### 4.1.1 用户管理
```bash
# 查看现有用户
sqlite3 server/data/users.db "SELECT * FROM users;"

# 添加新用户
python3 -c "
from auth_store import AuthStore
store = AuthStore('server/data/users.db')
store.add_user('newuser', 'password123')
print('用户添加成功')
"

# 修改用户密码
python3 -c "
from auth_store import AuthStore
store = AuthStore('server/data/users.db')
store.update_password('username', 'newpassword')
print('密码修改成功')
"

# 删除用户
python3 -c "
from auth_store import AuthStore
store = AuthStore('server/data/users.db')
store.delete_user('username')
print('用户删除成功')
"
```

#### 4.1.2 证书管理
```bash
# 查看证书信息
openssl x509 -in server/data/certs/server.crt -text -noout

# 检查证书有效期
openssl x509 -in server/data/certs/server.crt -dates -noout

# 生成新证书
cd server
python3 -c "
from cert_util import generate_self_signed_cert
generate_self_signed_cert(common_name='vpn.example.com', days=365)
"
```

### 4.2 客户端配置

#### 4.2.1 Windows 客户端配置
```json
// 配置文件位置: %APPDATA%\vpnproxy\config.json
{
  "server_host": "vpn.example.com",
  "server_port": 18443,
  "username": "your_username",
  "ca_cert_path": "C:\\path\\to\\server.crt",
  "socks_port": 1080,
  "auto_connect": false,
  "auto_start": false,
  "theme": "dark"
}
```

#### 4.2.2 Android 客户端配置
```kotlin
// 配置存储在 SharedPreferences 中
val prefs = getSharedPreferences("vpn_config", Context.MODE_PRIVATE)

// 默认配置
val defaultConfig = mapOf(
    "server_host" to "",
    "server_port" to 18443,
    "username" to "",
    "socks_port" to 1080,
    "auto_connect" to false,
    "use_system_dns" to true
)
```

## 5. 监控和维护

### 5.1 服务监控

#### 5.1.1 系统状态检查
```bash
# 检查服务状态
sudo systemctl status vpn-proxy.service

# 查看服务日志
sudo journalctl -u vpn-proxy.service -f

# 查看应用日志
tail -f /opt/vpn-proxy/logs/server.log

# 检查端口监听
sudo netstat -tlnp | grep 18443

# 检查连接数
ss -tunap | grep 18443 | wc -l
```

#### 5.1.2 性能监控
```bash
# CPU 和内存使用
top -p $(pgrep -f "python server/run.py")

# 网络流量
iftop -i eth0 -f "port 18443"

# 磁盘使用
df -h /opt
du -sh /opt/vpn-proxy/*
```

### 5.2 备份和恢复

#### 5.2.1 数据备份
```bash
#!/bin/bash
# backup_vpn.sh

BACKUP_DIR="/backup/vpn-proxy"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE

# 备份数据库
cp /opt/vpn-proxy/server/data/users.db $BACKUP_DIR/$DATE/

# 备份证书
cp -r /opt/vpn-proxy/server/data/certs $BACKUP_DIR/$DATE/

# 备份配置
cp /opt/vpn-proxy/config.yaml $BACKUP_DIR/$DATE/

# 压缩备份
tar -czf $BACKUP_DIR/vpn-backup-$DATE.tar.gz -C $BACKUP_DIR/$DATE .

# 清理临时文件
rm -rf $BACKUP_DIR/$DATE

# 保留最近7天备份
find $BACKUP_DIR -name "vpn-backup-*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/vpn-backup-$DATE.tar.gz"
```

#### 5.2.2 数据恢复
```bash
#!/bin/bash
# restore_vpn.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件>"
    exit 1
fi

# 停止服务
sudo systemctl stop vpn-proxy.service

# 解压备份
tar -xzf $BACKUP_FILE -C /tmp/vpn-restore

# 恢复数据
cp /tmp/vpn-restore/users.db /opt/vpn-proxy/server/data/
cp -r /tmp/vpn-restore/certs/* /opt/vpn-proxy/server/data/certs/
cp /tmp/vpn-restore/config.yaml /opt/vpn-proxy/

# 设置权限
chown -R vpnproxy:vpnproxy /opt/vpn-proxy/server/data

# 清理临时文件
rm -rf /tmp/vpn-restore

# 启动服务
sudo systemctl start vpn-proxy.service

echo "恢复完成"
```

### 5.3 故障排除

#### 5.3.1 常见问题
```bash
# 1. 服务无法启动
# 检查日志
sudo journalctl -u vpn-proxy.service -n 50

# 2. 证书问题
# 检查证书权限
ls -la /opt/vpn-proxy/server/data/certs/

# 3. 端口被占用
sudo lsof -i :18443

# 4. 连接问题
# 测试端口连通性
telnet vpn.example.com 18443
nc -zv vpn.example.com 18443

# 5. 性能问题
# 监控资源使用
htop
iotop
```

#### 5.3.2 调试模式
```bash
# 以调试模式运行
cd /opt/vpn-proxy
source venv/bin/activate
python server/run.py --debug --log-level DEBUG

# 客户端调试
# Windows: 添加 --debug 参数
# Android: 启用开发者选项，查看 Logcat
```

## 6. 安全加固

### 6.1 系统安全
```bash
# 1. 定期更新系统
sudo apt update && sudo apt upgrade -y

# 2. 配置 SSH 密钥认证
# 禁用密码登录
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 3. 配置 fail2ban
sudo apt install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 4. 配置防火墙
sudo ufw --force enable
```

### 6.2 应用安全
```bash
# 1. 使用非root用户运行
sudo chown -R vpnproxy:vpnproxy /opt/vpn-proxy

# 2. 限制文件权限
chmod 600 /opt/vpn