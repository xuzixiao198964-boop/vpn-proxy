# VPN 代理隧道 - API 文档

## 概述

本文档描述了 VPN 代理隧道项目的 API 接口，包括服务端 API、客户端 API 和内部组件 API。

## 1. 服务端 API

### 1.1 认证 API

#### 1.1.1 用户认证
```python
# 请求格式
{
    "username": "string",  # 用户名
    "password": "string",  # 密码
    "client_type": "windows|android"  # 客户端类型
}

# 响应格式
{
    "success": true|false,  # 认证结果
    "message": "string",    # 结果消息
    "session_id": "string",  # 会话ID（认证成功时）
    "expires_at": 1234567890  # 过期时间戳
}

# 错误响应
{
    "success": false,
    "error": "invalid_credentials|user_not_found|account_locked",
    "message": "详细错误信息"
}
```

#### 1.1.2 会话验证
```python
# 请求头
Authorization: Bearer <session_id>

# 响应
{
    "valid": true|false,
    "user_id": "string",
    "username": "string",
    "permissions": ["connect", "disconnect"]
}
```

### 1.2 隧道管理 API

#### 1.2.1 建立隧道连接
```python
# 请求
{
    "session_id": "string",
    "client_info": {
        "version": "1.0.0",
        "platform": "windows|android",
        "device_id": "string"
    }
}

# 响应
{
    "tunnel_id": "string",
    "server_port": 18443,
    "max_bandwidth": 1000000,  # 1Mbps
    "settings": {
        "keepalive_interval": 30,
        "timeout": 300
    }
}
```

#### 1.2.2 关闭隧道连接
```python
# 请求
{
    "tunnel_id": "string",
    "reason": "user_request|timeout|error"
}

# 响应
{
    "success": true,
    "bytes_sent": 123456,
    "bytes_received": 654321,
    "duration": 3600
}
```

### 1.3 统计 API

#### 1.3.1 获取连接统计
```python
# 请求
GET /api/stats/connections

# 响应
{
    "total_connections": 10,
    "active_connections": 5,
    "connections": [
        {
            "tunnel_id": "string",
            "username": "string",
            "connected_at": 1234567890,
            "bytes_sent": 123456,
            "bytes_received": 654321,
            "client_info": {...}
        }
    ]
}
```

#### 1.3.2 获取系统状态
```python
# 请求
GET /api/stats/system

# 响应
{
    "cpu_usage": 15.5,
    "memory_usage": 45.2,
    "network_usage": {
        "inbound": 1234567,
        "outbound": 7654321
    },
    "uptime": 86400,
    "version": "1.0.0"
}
```

## 2. 客户端 API

### 2.1 Windows 客户端 API

#### 2.1.1 配置管理
```python
class VPNConfig:
    """VPN 配置类"""
    
    def __init__(self):
        self.server_host = "vpn.example.com"
        self.server_port = 18443
        self.username = ""
        self.password = ""  # 不持久化存储
        self.ca_cert_path = ""
        self.socks_port = 1080
        self.auto_connect = False
        self.auto_start = False
    
    def save(self, filepath: str):
        """保存配置到文件"""
        pass
    
    def load(self, filepath: str):
        """从文件加载配置"""
        pass
    
    def validate(self) -> bool:
        """验证配置有效性"""
        pass
```

#### 2.1.2 连接管理
```python
class VPNConnection:
    """VPN 连接管理类"""
    
    def connect(self, config: VPNConfig) -> bool:
        """建立 VPN 连接"""
        pass
    
    def disconnect(self):
        """断开 VPN 连接"""
        pass
    
    def get_status(self) -> dict:
        """获取连接状态"""
        return {
            "connected": True|False,
            "server": "string",
            "duration": 123,
            "bytes_sent": 123456,
            "bytes_received": 654321,
            "local_address": "127.0.0.1:1080"
        }
    
    def reconnect(self):
        """重新连接"""
        pass
```

### 2.2 Android 客户端 API

#### 2.2.1 VPN 服务
```kotlin
class TunVpnService : VpnService() {
    /**
     * 建立 VPN 连接
     */
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // 建立 VPN 连接
        establishVpn()
        startTunnel()
        return START_STICKY
    }
    
    /**
     * 建立 VPN 接口
     */
    private fun establishVpn(): Boolean {
        val builder = Builder()
        builder.setSession("VPN Proxy")
        builder.addAddress("10.0.0.2", 32)
        builder.addRoute("0.0.0.0", 0)
        builder.addDnsServer("8.8.8.8")
        builder.setMtu(1500)
        
        val interface = builder.establish()
        return interface != null
    }
    
    /**
     * 启动隧道
     */
    private fun startTunnel() {
        // 启动 tun2socks 和隧道连接
    }
}
```

#### 2.2.2 配置管理
```kotlin
data class VpnConfig(
    val serverHost: String = "",
    val serverPort: Int = 18443,
    val username: String = "",
    val password: String = "",
    val socksPort: Int = 1080,
    val autoConnect: Boolean = false,
    val useSystemDns: Boolean = true
)

class ConfigManager(context: Context) {
    private val prefs = context.getSharedPreferences("vpn_config", Context.MODE_PRIVATE)
    
    fun saveConfig(config: VpnConfig) {
        prefs.edit().apply {
            putString("server_host", config.serverHost)
            putInt("server_port", config.serverPort)
            putString("username", config.username)
            putInt("socks_port", config.socksPort)
            putBoolean("auto_connect", config.autoConnect)
            apply()
        }
    }
    
    fun loadConfig(): VpnConfig {
        return VpnConfig(
            serverHost = prefs.getString("server_host", "") ?: "",
            serverPort = prefs.getInt("server_port", 18443),
            username = prefs.getString("username", "") ?: "",
            socksPort = prefs.getInt("socks_port", 1080),
            autoConnect = prefs.getBoolean("auto_connect", false)
        )
    }
}
```

## 3. 内部组件 API

### 3.1 隧道协议

#### 3.1.1 数据帧格式
```
+----------------+----------------+----------------+----------------+
|  版本 (1字节)   |  类型 (1字节)   |  长度 (2字节)   |  数据 (变长)    |
+----------------+----------------+----------------+----------------+

版本: 0x01
类型:
  0x01 = 控制帧 (认证、心跳等)
  0x02 = 数据帧 (隧道数据)
  0x03 = 错误帧
长度: 数据部分长度 (大端序)
数据: 根据类型不同而不同
```

#### 3.1.2 控制帧类型
```python
CONTROL_TYPES = {
    0x01: "AUTH_REQUEST",      # 认证请求
    0x02: "AUTH_RESPONSE",     # 认证响应
    0x03: "HEARTBEAT",         # 心跳
    0x04: "HEARTBEAT_ACK",     # 心跳确认
    0x05: "DISCONNECT",        # 断开连接
    0x06: "STATS_REQUEST",     # 统计请求
    0x07: "STATS_RESPONSE",    # 统计响应
    0x08: "CONFIG_UPDATE",     # 配置更新
}
```

### 3.2 证书管理 API

#### 3.2.1 证书生成
```python
def generate_certificate(
    common_name: str,
    days_valid: int = 365,
    key_size: int = 2048
) -> tuple:
    """
    生成证书和私钥
    
    Args:
        common_name: 证书通用名
        days_valid: 有效期天数
        key_size: 密钥大小
    
    Returns:
        (cert_pem, key_pem) 证书和私钥的PEM格式
    """
    pass
```

#### 3.2.2 证书验证
```python
def verify_certificate(
    cert_pem: str,
    ca_cert_pem: str
) -> bool:
    """
    验证证书
    
    Args:
        cert_pem: 待验证证书
        ca_cert_pem: CA证书
    
    Returns:
        验证结果
    """
    pass
```

## 4. WebSocket API（未来扩展）

### 4.1 实时监控
```javascript
// 连接WebSocket
const ws = new WebSocket('wss://vpn.example.com/ws/monitor');

// 订阅连接事件
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'connections'
}));

// 接收实时数据
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('实时连接数据:', data);
};
```

### 4.2 管理操作
```javascript
// 断开指定连接
ws.send(JSON.stringify({
    action: 'disconnect',
    tunnel_id: 'abc123',
    reason: 'admin_request'
}));

// 更新用户配置
ws.send(JSON.stringify({
    action: 'update_user',
    user_id: 'user123',
    updates: {
        max_bandwidth: 5000000,
        enabled: true
    }
}));
```

## 5. 错误代码

### 5.1 通用错误代码
| 代码 | 描述 | 解决方案 |
|------|------|----------|
| 1001 | 认证失败 | 检查用户名密码 |
| 1002 | 会话过期 | 重新登录 |
| 1003 | 权限不足 | 检查用户权限 |
| 1004 | 参数错误 | 检查请求参数 |
| 1005 | 服务器错误 | 联系管理员 |

### 5.2 网络错误代码
| 代码 | 描述 | 解决方案 |
|------|------|----------|
| 2001 | 连接超时 | 检查网络连接 |
| 2002 | 证书错误 | 检查证书配置 |
| 2003 | 协议错误 | 更新客户端版本 |
| 2004 | 带宽限制 | 减少并发连接 |
| 2005 | 服务器繁忙 | 稍后重试 |

### 5.3 客户端错误代码
| 代码 | 描述 | 解决方案 |
|------|------|----------|
| 3001 | 配置错误 | 检查客户端配置 |
| 3002 | 资源不足 | 释放系统资源 |
| 3003 | 权限错误 | 检查系统权限 |
| 3004 | 版本不兼容 | 更新软件版本 |
| 3005 | 本地错误 | 重启客户端 |

## 6. 版本兼容性

### 6.1 API 版本
```
v1.0 (当前): 基础功能
v1.1 (计划): 增强统计和监控
v2.0 (未来): Web管理界面和集群支持
```

### 6.2 向后兼容性
- 所有 API 变更保持向后兼容
- 弃用的 API 会有足够长的过渡期
- 版本信息在响应头中返回

### 6.3 客户端兼容性
| 客户端版本 | 最低服务端版本 | 推荐服务端版本 |
|------------|----------------|----------------|
| 1.0.x | 1.0.0 | 1.0.0+ |
| 1.1.x | 1.0.0 | 1.1.0+ |
| 2.0.x | 1.1.0 | 2.0.0+ |

## 7. 安全注意事项

### 7.1 API 安全
- 所有 API 必须使用 HTTPS/TLS
- 敏感操作需要重新认证
- 实施速率限制防止滥用
- 记录所有 API 访问日志

### 7.2 数据安全
- 密码等敏感数据必须加密传输
- 用户数据必须隔离存储
- 定期清理过期数据
- 实施数据备份机制

### 7.3 访问控制
- 基于角色的访问控制 (RBAC)
- 最小权限原则
- 会话管理和超时
- 登录失败锁定机制

## 8. 性能指标

### 8.1 API 性能要求
| 指标 | 要求 | 监控方法 |
|------|------|----------|
| 响应时间 | < 100ms (P95) | 应用性能监控 |
| 可用性 | > 99.9% | 健康检查 |
| 吞吐量 | > 1000 req/s | 负载测试 |
| 错误率 | < 0.1% | 错误日志分析 |

### 8.2 监控端点
```
GET /health          # 健康检查
GET /metrics         # Prometheus指标
GET /debug/pprof     # 性能分析
GET /version         # 版本信息
```

## 9. 示例代码

### 9.1 Python 客户端示例
```python
import requests
import json

class VPNClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def authenticate(self, username, password):
        """用户认证"""
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={
                "username": username,
                "password": password,
                "client_type": "python"
            }
        )
        return response.json()
    
    def get_stats(self):
        """获取统计信息"""
        response = self.session.get(f"{self.base_url}/api/stats/system")
        return response.json()
    
    def disconnect_all(self):
        """断开所有连接"""
        response = self.session.post(
            f"{self.base_url}/api/tunnel/disconnect_all",
            json={"reason": "admin_request"}
        )
        return response.json()
```

### 9.2 JavaScript 管理界面示例
```javascript
// 管理界面API封装
class VPNAdminAPI {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }
    
    async getConnections() {
        const response = await fetch(`${this.baseURL}/api/stats/connections`);
        return await response.json();
    }
    
    async disconnectConnection(tunnelId, reason) {
        const response = await fetch(`${this.baseURL}/api/tunnel/disconnect`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tunnel_id: tunnelId, reason: reason})
        });
        return await response.json();
    }
    
    async updateUser(userId, updates) {
        const response = await fetch(`${this.baseURL}/api/users/${userId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates)
        });
        return await response.json();
    }
}
```

## 10. 附录

### 10.1 相关链接
- [OpenAPI 规范](https://swagger.io/specification/)
- [REST API 设计指南](https://restfulapi.net/)
- [TLS 最佳实践](https://cheatsheetseries.owasp.org/cheatsheets/TLS_Cheat_Sheet.html)

### 10.2 工具推荐
- **API 测试**: Postman, Insomnia
- **文档生成**: Swagger/OpenAPI
- **监控工具**: Prometheus, Grafana
- **负载测试**: k6, Apache JMeter

### 10.3 支持与反馈
- 问题反馈: GitHub Issues
- 功能请求: GitHub Discussions
- 安全报告: 安全邮件地址
- 文档问题: 提交 PR 修正

---
*API 版本: 1.0.0*
*最后更新: 2026-03-26*
*文档状态: 正式版*