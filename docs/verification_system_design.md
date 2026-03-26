# 验证码系统设计文档

## 概述

本文档描述 VPN 代理隧道项目的验证码系统设计，包括用户注册、登录、验证码发送和验证等完整流程。

## 1. 系统架构

### 1.1 组件架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端         │    │     服务端       │    │  第三方服务     │
│  (Windows/Android) │    │  (VPN Server)   │    │  (短信/邮箱)    │
│                 │    │                 │    │                 │
│  • 注册界面     │    │  • 用户管理     │    │  • 短信网关     │
│  • 登录界面     │────┤  • 验证码生成   │────┤  • 邮箱服务     │
│  • 验证码输入   │    │  • 验证码验证   │    │  • 发送服务     │
│  • 自动连接     │    │  • 会话管理     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 数据流
1. 客户端发起注册/登录请求
2. 服务端生成验证码并发送到第三方服务
3. 用户收到验证码并输入
4. 服务端验证验证码
5. 验证通过后建立用户会话
6. 客户端自动连接VPN

## 2. 注册流程设计

### 2.1 注册步骤
```
1. 用户输入用户名、密码、邮箱/手机号
2. 客户端验证输入格式
3. 服务端检查用户名和邮箱/手机号是否已存在
4. 服务端生成6位数字验证码
5. 通过短信/邮箱发送验证码
6. 用户输入验证码
7. 服务端验证验证码
8. 创建用户账户并加密存储密码
9. 返回注册成功，自动登录
10. 客户端自动连接VPN
```

### 2.2 注册API设计
```python
# 1. 检查用户是否存在
POST /api/auth/check-user
{
    "username": "string",
    "email": "string",  # 可选
    "phone": "string"   # 可选
}

# 2. 发送验证码
POST /api/auth/send-code
{
    "username": "string",
    "email": "string",  # 二选一
    "phone": "string",  # 二选一
    "type": "register"  # register|login|reset
}

# 3. 注册用户
POST /api/auth/register
{
    "username": "string",
    "password": "string",
    "email": "string",  # 可选
    "phone": "string",  # 可选
    "code": "string"    # 验证码
}
```

## 3. 登录流程设计

### 3.1 登录方式
1. **用户名密码登录**
   - 输入用户名和密码
   - 服务端验证凭证
   - 返回登录令牌

2. **验证码登录**
   - 输入用户名/手机号/邮箱
   - 请求发送验证码
   - 输入验证码登录

3. **自动登录**
   - 客户端保存加密的登录令牌
   - 启动时自动验证令牌
   - 令牌有效则自动连接VPN

### 3.2 登录API设计
```python
# 1. 密码登录
POST /api/auth/login
{
    "username": "string",
    "password": "string"
}

# 2. 验证码登录
POST /api/auth/login-with-code
{
    "identifier": "string",  # 用户名/邮箱/手机号
    "code": "string"         # 验证码
}

# 3. 验证令牌
POST /api/auth/verify-token
{
    "token": "string"
}
```

## 4. 验证码系统设计

### 4.1 验证码生成
```python
class VerificationCodeSystem:
    def generate_code(self, length=6):
        """生成数字验证码"""
        import random
        return ''.join(str(random.randint(0, 9)) for _ in range(length))
    
    def store_code(self, identifier, code, code_type, expires_in=300):
        """存储验证码到数据库或缓存"""
        # 存储到 Redis 或数据库
        # key: "code:{type}:{identifier}"
        # value: code
        # 过期时间: expires_in 秒（默认5分钟）
        pass
    
    def verify_code(self, identifier, code, code_type):
        """验证验证码"""
        # 从存储中获取验证码
        # 比较输入的验证码
        # 验证成功后删除验证码
        pass
```

### 4.2 验证码发送
```python
class CodeSender:
    def send_sms(self, phone, code):
        """发送短信验证码"""
        # 调用第三方短信服务
        # 如阿里云、腾讯云短信服务
        pass
    
    def send_email(self, email, code):
        """发送邮箱验证码"""
        # 使用 SMTP 发送邮件
        # 邮件模板包含验证码
        pass
    
    def send_code(self, identifier, code, code_type):
        """根据标识符类型发送验证码"""
        if '@' in identifier:
            self.send_email(identifier, code)
        else:
            self.send_sms(identifier, code)
```

### 4.3 安全限制
```python
class SecurityLimiter:
    def __init__(self):
        self.rate_limits = {
            'send_code': 5,      # 每小时最多发送5次
            'verify_code': 10,   # 每小时最多验证10次
            'login_attempts': 5  # 连续失败5次锁定
        }
    
    def check_rate_limit(self, ip, action):
        """检查频率限制"""
        # 使用 Redis 记录IP和动作的频率
        # 返回是否超过限制
        pass
    
    def record_attempt(self, ip, action, success):
        """记录尝试"""
        # 记录成功/失败的尝试
        # 用于锁定机制
        pass
```

## 5. 数据库设计

### 5.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);
```

### 5.2 验证码表 (verification_codes)
```sql
CREATE TABLE verification_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier VARCHAR(100) NOT NULL,  -- 手机号或邮箱
    code VARCHAR(10) NOT NULL,
    code_type VARCHAR(20) NOT NULL,    -- register|login|reset
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT 0,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_codes_identifier ON verification_codes(identifier);
CREATE INDEX idx_codes_expires ON verification_codes(expires_at);
```

### 5.3 会话表 (sessions)
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

## 6. 客户端实现

### 6.1 Windows 客户端
```python
class WindowsAuthClient:
    def __init__(self):
        self.config_file = "auth_config.json"
        self.token = None
    
    def register(self, username, password, email=None, phone=None):
        """用户注册"""
        # 1. 检查用户是否存在
        # 2. 发送验证码
        # 3. 输入验证码
        # 4. 完成注册
        # 5. 保存登录状态
        # 6. 自动连接VPN
        pass
    
    def login(self, username, password=None, code=None):
        """用户登录"""
        if code:
            # 验证码登录
            result = self.login_with_code(username, code)
        else:
            # 密码登录
            result = self.login_with_password(username, password)
        
        if result.success:
            self.save_login_state(result.token)
            self.auto_connect_vpn()
        return result
    
    def auto_login(self):
        """自动登录"""
        if self.has_saved_token():
            token = self.load_token()
            if self.verify_token(token):
                self.auto_connect_vpn()
                return True
        return False
```

### 6.2 Android 客户端
```kotlin
class AndroidAuthManager(context: Context) {
    private val prefs = context.getSharedPreferences("auth_prefs", Context.MODE_PRIVATE)
    
    fun register(username: String, password: String, phone: String) {
        // 1. 验证输入格式
        // 2. 请求发送验证码
        // 3. 显示验证码输入界面
        // 4. 提交注册
        // 5. 保存登录状态
        // 6. 启动VPN连接
    }
    
    fun loginWithCode(identifier: String, code: String) {
        // 验证码登录
        // 成功后保存会话
        // 自动启动VPN服务
    }
    
    fun autoConnect() {
        // 检查是否有有效会话
        // 自动连接VPN
    }
}
```

## 7. 安全考虑

### 7.1 密码安全
- 使用 bcrypt 或 Argon2 加密密码
- 密码最小长度8位，包含字母和数字
- 禁止使用常见弱密码

### 7.2 验证码安全
- 验证码6位数字，5分钟有效
- 同一IP每小时最多发送5次验证码
- 验证码验证失败3次后需要重新获取
- 验证成功后立即删除验证码

### 7.3 会话安全
- 使用 JWT 或类似机制管理会话
- 会话有效期24小时
- 支持会话续期
- 记录登录IP和设备信息

### 7.4 防刷机制
- IP级别频率限制
- 用户级别频率限制
- 验证码图形验证（可选）
- 行为分析检测异常

## 8. 错误处理

### 8.1 常见错误码
```python
ERROR_CODES = {
    "USER_EXISTS": 1001,      # 用户已存在
    "INVALID_CODE": 1002,     # 验证码错误
    "CODE_EXPIRED": 1003,     # 验证码过期
    "RATE_LIMITED": 1004,     # 频率限制
    "ACCOUNT_LOCKED": 1005,   # 账户锁定
    "INVALID_CREDENTIALS": 1006,  # 凭证错误
    "NETWORK_ERROR": 1007,    # 网络错误
    "SERVER_ERROR": 1008,     # 服务器错误
}
```

### 8.2 错误处理策略
- 客户端显示友好的错误信息
- 记录详细的错误日志
- 提供重试机制
- 支持错误恢复

## 9. 测试计划

### 9.1 单元测试
- 验证码生成和验证测试
- 密码加密和验证测试
- 频率限制测试
- 会话管理测试

### 9.2 集成测试
- 完整的注册流程测试
- 登录流程测试
- 验证码发送测试
- 自动连接测试

### 9.3 压力测试
- 并发注册测试
- 并发登录测试
- 验证码发送压力测试
- 会话管理压力测试

## 10. 部署配置

### 10.1 服务端配置
```yaml
auth:
  enabled: true
  require_verification: true
  code_expires: 300  # 5分钟
  max_attempts: 5    # 最大尝试次数
  lock_duration: 1800  # 锁定30分钟
  
sms:
  provider: "aliyun"  # aliyun|tencent
  app_key: "your_app_key"
  app_secret: "your_app_secret"
  template_id: "your_template_id"
  
email:
  smtp_host: "smtp.example.com"
  smtp_port: 587
  username: "noreply@example.com"
  password: "your_password"
  from_address: "noreply@example.com"
```

### 10.2 客户端配置
```json
{
  "auth_server": "https://vpn.example.com",
  "auto_login": true,
  "remember_me": true,
  "session_timeout": 86400,
  "retry_count": 3,
  "retry_delay": 1000
}
```

---
*文档版本：1.0*
*最后更新：2026-03-26*
*文档状态：草案*