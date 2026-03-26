# VPN 代理隧道项目 - 概要设计文档

## 1. 项目概述

### 1.1 项目目标
开发一个跨平台的 VPN 代理解决方案，提供完整的用户注册登录验证码系统，登录后自动连接 VPN，支持 Windows 和 Android 客户端。

### 1.2 设计原则
- **简单直接**：减少中间件依赖，避免容器化
- **裸机运行**：直接在操作系统上运行
- **安全性优先**：完整的认证和加密体系
- **用户体验**：注册登录后自动连接，减少用户操作

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Windows客户端  │    │     服务端       │    │   Android客户端  │
│                 │    │                 │    │                 │
│  • 图形界面     │    │  • 认证服务     │    │  • 移动界面     │
│  • 注册登录     │────┤  • 验证码服务   │────┤  • 注册登录     │
│  • 自动连接     │    │  • VPN隧道      │    │  • 自动连接     │
│  • SOCKS5代理   │    │  • 流量转发     │    │  • VPN服务      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 技术选型
| 组件 | 技术栈 | 说明 |
|------|--------|------|
| **服务端** | Python 3.8+, OpenSSL, SQLite | 轻量级，无需中间件 |
| **Windows客户端** | Python 3.8+, Tkinter, PySocks | 原生界面，直接运行 |
| **Android客户端** | Kotlin, Android SDK, Go (tun2socks) | 原生开发，性能优化 |
| **数据库** | SQLite | 嵌入式，无需单独服务 |
| **验证码服务** | 内置SMTP/第三方短信API | 根据配置选择 |

## 3. 模块设计

### 3.1 服务端模块
```
vpn_server/
├── auth/              # 认证模块
│   ├── user_manager.py    # 用户管理
│   ├── code_service.py    # 验证码服务
│   └── session_manager.py # 会话管理
├── tunnel/            # 隧道模块
│   ├── tls_tunnel.py      # TLS隧道
│   └── traffic_forward.py # 流量转发
├── database/          # 数据库模块
│   └── sqlite_db.py       # SQLite操作
└── main.py           # 主程序
```

### 3.2 Windows客户端模块
```
windows_client/
├── ui/               # 界面模块
│   ├── main_window.py    # 主窗口
│   ├── login_dialog.py   # 登录对话框
│   └── register_dialog.py # 注册对话框
├── auth/             # 认证模块
│   ├── auth_client.py    # 认证客户端
│   └── token_manager.py  # 令牌管理
├── tunnel/           # 隧道模块
│   └── vpn_client.py     # VPN客户端
└── main.py          # 主程序
```

### 3.3 Android客户端模块
```
android/
├── app/src/main/java/com/vpnproxy/app/
│   ├── auth/            # 认证模块
│   │   ├── AuthManager.kt      # 认证管理
│   │   └── TokenStorage.kt     # 令牌存储
│   ├── ui/             # 界面模块
│   │   ├── LoginActivity.kt    # 登录界面
│   │   └── MainActivity.kt     # 主界面
│   └── vpn/            # VPN模块
│       └── TunVpnService.kt    # VPN服务
└── tun2socks-go/       # Go隧道模块
```

## 4. 数据流设计

### 4.1 注册流程
```
1. 客户端 → 服务端: 检查用户是否存在
2. 服务端 → 客户端: 用户可用性结果
3. 客户端 → 服务端: 请求发送验证码
4. 服务端 → 第三方: 发送验证码(短信/邮箱)
5. 客户端 → 服务端: 提交注册信息+验证码
6. 服务端 → 客户端: 注册结果+登录令牌
7. 客户端: 保存令牌，自动连接VPN
```

### 4.2 登录流程
```
1. 客户端 → 服务端: 登录请求(密码或验证码)
2. 服务端 → 客户端: 登录结果+会话令牌
3. 客户端: 保存会话，自动连接VPN
```

### 4.3 VPN连接流程
```
1. 客户端: 检查有效会话
2. 客户端 → 服务端: 建立TLS连接
3. 服务端: 验证用户权限
4. 双方: 建立加密隧道
5. 客户端: 启动本地SOCKS5代理(Windows)或VPN服务(Android)
```

## 5. 数据库设计

### 5.1 核心表结构
```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 验证码表
CREATE TABLE verification_codes (
    id INTEGER PRIMARY KEY,
    identifier TEXT NOT NULL,
    code TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- 会话表
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 6. 接口设计

### 6.1 RESTful API
```
认证相关:
POST /api/auth/check-user      # 检查用户
POST /api/auth/send-code       # 发送验证码
POST /api/auth/register        # 用户注册
POST /api/auth/login           # 用户登录
POST /api/auth/verify-token    # 验证令牌

VPN相关:
POST /api/vpn/connect          # 连接VPN
POST /api/vpn/disconnect       # 断开VPN
GET  /api/vpn/status           # 获取状态
```

### 6.2 数据格式
```json
// 注册请求
{
    "username": "user123",
    "password": "secure_password",
    "email": "user@example.com",
    "code": "123456"
}

// 登录响应
{
    "success": true,
    "token": "jwt_token_here",
    "user": {
        "id": 1,
        "username": "user123"
    }
}
```

## 7. 安全设计

### 7.1 加密方案
- **传输加密**: TLS 1.2+ (AES-256-GCM)
- **密码存储**: bcrypt (cost=12)
- **令牌安全**: JWT with HMAC-SHA256
- **验证码**: 6位数字，5分钟有效期

### 7.2 防护机制
- **频率限制**: IP级别请求限制
- **账户锁定**: 连续5次失败锁定30分钟
- **验证码防刷**: 同一用户每小时最多5次
- **会话管理**: 24小时有效期，支持续期

## 8. 部署设计

### 8.1 服务端部署
```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3 python3-pip openssl

# 2. 部署代码
cd /opt/vpn-proxy
git clone https://github.com/your-repo/vpn-proxy.git

# 3. 安装Python依赖
pip3 install -r requirements.txt

# 4. 配置服务
cp config.example.yaml config.yaml
# 编辑配置文件

# 5. 启动服务
python3 server/main.py --daemon
```

### 8.2 客户端部署
- **Windows**: 打包为exe，一键安装
- **Android**: 生成APK，直接安装

### 8.3 配置文件
```yaml
server:
  host: 0.0.0.0
  port: 18443
  ssl_cert: certs/server.crt
  ssl_key: certs/server.key

auth:
  require_verification: true
  code_expires: 300
  
database:
  path: data/vpn.db

logging:
  level: INFO
  file: logs/server.log
```

## 9. 性能设计

### 9.1 资源预估
| 资源 | 服务端 | Windows客户端 | Android客户端 |
|------|--------|---------------|---------------|
| CPU | 1核心(100用户) | <5% (空闲) | <10% (空闲) |
| 内存 | 200MB | 50MB | 100MB |
| 存储 | 1GB | 100MB | 50MB |

### 9.2 并发处理
- **连接数**: 支持100+并发用户
- **吞吐量**: 100Mbps带宽
- **延迟**: <300ms (公网)

## 10. 容错设计

### 10.1 故障处理
- **网络中断**: 自动重连机制
- **服务重启**: 会话恢复
- **数据库故障**: 自动修复或重建
- **客户端异常**: 优雅退出和恢复

### 10.2 监控告警
- **健康检查**: 定期自检
- **日志记录**: 详细操作日志
- **错误报警**: 关键错误通知
- **性能监控**: 资源使用监控

## 11. 测试策略

### 11.1 测试类型
- **单元测试**: 模块功能测试
- **集成测试**: 模块间接口测试
- **系统测试**: 完整流程测试
- **压力测试**: 性能负载测试

### 11.2 测试工具
- Python: unittest, pytest
- Android: Espresso, JUnit
- 性能: Apache Bench, wrk

## 12. 开发计划

### 12.1 第一阶段 (2周)
- 基础认证模块
- 验证码服务
- 数据库设计

### 12.2 第二阶段 (3周)
- VPN隧道核心
- Windows客户端界面
- Android客户端基础

### 12.3 第三阶段 (2周)
- 自动连接逻辑
- 错误处理优化
- 性能调优

### 12.4 第四阶段 (1周)
- 测试验证
- 文档完善
- 部署准备

---
*文档版本: 1.0*
*最后更新: 2026-03-26*
*设计状态: 草案*