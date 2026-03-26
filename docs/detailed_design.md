# VPN 代理隧道项目 - 详细设计文档

## 1. 认证系统详细设计

### 1.1 用户管理模块

#### 1.1.1 UserManager 类设计
```python
class UserManager:
    def __init__(self, db_path):
        self.db = SQLiteDatabase(db_path)
    
    def check_user_exists(self, username, email=None, phone=None):
        """检查用户是否已存在"""
        query = """
        SELECT COUNT(*) FROM users 
        WHERE username = ? OR email = ? OR phone = ?
        """
        result = self.db.execute(query, (username, email, phone))
        return result[0][0] > 0
    
    def create_user(self, username, password, email=None, phone=None):
        """创建新用户"""
        # 密码加密
        password_hash = self._hash_password(password)
        
        query = """
        INSERT INTO users (username, password_hash, email, phone, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """
        user_id = self.db.execute_insert(query, (username, password_hash, email, phone))
        
        # 生成初始会话
        token = self._generate_token(user_id)
        return user_id, token
    
    def authenticate_user(self, username, password):
        """用户认证"""
        query = "SELECT id, password_hash FROM users WHERE username = ? AND is_active = 1"
        result = self.db.execute(query, (username,))
        
        if not result:
            return None
        
        user_id, stored_hash = result[0]
        if self._verify_password(password, stored_hash):
            # 更新最后登录时间
            self._update_last_login(user_id)
            # 生成新令牌
            token = self._generate_token(user_id)
            return user_id, token
        
        return None
    
    def _hash_password(self, password):
        """使用bcrypt加密密码"""
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def _verify_password(self, password, stored_hash):
        """验证密码"""
        import bcrypt
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    
    def _generate_token(self, user_id):
        """生成JWT令牌"""
        import jwt
        import datetime
        
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }
        
        # 从配置读取密钥
        secret_key = self._get_secret_key()
        return jwt.encode(payload, secret_key, algorithm='HS256')
```

#### 1.1.2 数据库操作类
```python
class SQLiteDatabase:
    def __init__(self, db_path):
        import sqlite3
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        scripts = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                code TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        ]
        
        for script in scripts:
            self.conn.execute(script)
        self.conn.commit()
    
    def execute(self, query, params=()):
        """执行查询"""
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()
    
    def execute_insert(self, query, params=()):
        """执行插入操作"""
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid
```

### 1.2 验证码服务模块

#### 1.2.1 CodeService 类设计
```python
class CodeService:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.rate_limiter = RateLimiter(db)
    
    def send_verification_code(self, identifier, code_type='register'):
        """发送验证码"""
        # 检查频率限制
        if not self.rate_limiter.check_limit(identifier, 'send_code'):
            raise RateLimitError("发送频率过高，请稍后再试")
        
        # 生成验证码
        code = self._generate_code()
        
        # 存储验证码
        self._store_code(identifier, code, code_type)
        
        # 发送验证码
        if '@' in identifier:
            self._send_email_code(identifier, code, code_type)
        else:
            self._send_sms_code(identifier, code, code_type)
        
        return True
    
    def verify_code(self, identifier, code, code_type='register'):
        """验证验证码"""
        # 清理过期验证码
        self._clean_expired_codes()
        
        query = """
        SELECT id, expires_at FROM verification_codes 
        WHERE identifier = ? AND code = ? AND type = ? AND used = 0
        ORDER BY created_at DESC LIMIT 1
        """
        
        result = self.db.execute(query, (identifier, code, code_type))
        if not result:
            return False
        
        code_id, expires_at = result[0]
        
        # 检查是否过期
        from datetime import datetime
        if datetime.fromisoformat(expires_at) < datetime.now():
            return False
        
        # 标记为已使用
        self.db.execute("UPDATE verification_codes SET used = 1 WHERE id = ?", (code_id,))
        
        return True
    
    def _generate_code(self, length=6):
        """生成数字验证码"""
        import random
        return ''.join(str(random.randint(0, 9)) for _ in range(length))
    
    def _store_code(self, identifier, code, code_type):
        """存储验证码"""
        from datetime import datetime, timedelta
        
        expires_at = datetime.now() + timedelta(seconds=self.config['code_expires'])
        
        query = """
        INSERT INTO verification_codes (identifier, code, type, expires_at)
        VALUES (?, ?, ?, ?)
        """
        
        self.db.execute_insert(query, (identifier, code, code_type, expires_at.isoformat()))
    
    def _send_sms_code(self, phone, code, code_type):
        """发送短信验证码"""
        # 根据配置选择短信服务商
        provider = self.config.get('sms_provider', 'console')
        
        if provider == 'console':
            # 开发环境：打印到控制台
            print(f"[DEBUG] SMS验证码发送到 {phone}: {code}")
        elif provider == 'aliyun':
            self._send_aliyun_sms(phone, code, code_type)
        elif provider == 'tencent':
            self._send_tencent_sms(phone, code, code_type)
        else:
            raise ValueError(f"不支持的短信服务商: {provider}")
    
    def _send_email_code(self, email, code, code_type):
        """发送邮箱验证码"""
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        
        # 邮件内容
        subject = "VPN代理验证码"
        if code_type == 'register':
            content = f"您的注册验证码是：{code}，5分钟内有效"
        elif code_type == 'login':
            content = f"您的登录验证码是：{code}，5分钟内有效"
        else:
            content = f"您的验证码是：{code}，5分钟内有效"
        
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = self.config['email_from']
        msg['To'] = email
        
        # 发送邮件
        try:
            smtp = smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port'])
            smtp.starttls()
            smtp.login(self.config['email_user'], self.config['email_password'])
            smtp.send_message(msg)
            smtp.quit()
        except Exception as e:
            print(f"发送邮件失败: {e}")
            # 开发环境回退到控制台输出
            print(f"[DEBUG] Email验证码发送到 {email}: {code}")
```

#### 1.2.2 频率限制器
```python
class RateLimiter:
    def __init__(self, db):
        self.db = db
    
    def check_limit(self, identifier, action, window_seconds=3600, max_attempts=5):
        """检查频率限制"""
        from datetime import datetime, timedelta
        
        window_start = datetime.now() - timedelta(seconds=window_seconds)
        
        query = """
        SELECT COUNT(*) FROM rate_limits 
        WHERE identifier = ? AND action = ? AND created_at > ?
        """
        
        result = self.db.execute(query, (identifier, action, window_start.isoformat()))
        count = result[0][0] if result else 0
        
        if count >= max_attempts:
            return False
        
        # 记录本次尝试
        self._record_attempt(identifier, action)
        return True
    
    def _record_attempt(self, identifier, action):
        """记录尝试"""
        query = "INSERT INTO rate_limits (identifier, action) VALUES (?, ?)"
        self.db.execute_insert(query, (identifier, action))
```

### 1.3 会话管理模块

#### 1.3.1 SessionManager 类设计
```python
class SessionManager:
    def __init__(self, db, secret_key):
        self.db = db
        self.secret_key = secret_key
    
    def create_session(self, user_id, ip_address=None, user_agent=None):
        """创建新会话"""
        import jwt
        import datetime
        
        # 生成JWT令牌
        token = self._generate_jwt_token(user_id)
        
        # 计算过期时间
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        
        # 存储到数据库
        query = """
        INSERT INTO sessions (user_id, token, expires_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
        """
        
        session_id = self.db.execute_insert(
            query, (user_id, token, expires_at.isoformat(), ip_address, user_agent)
        )
        
        return token, expires_at
    
    def verify_session(self, token):
        """验证会话"""
        import jwt
        import datetime
        
        try:
            # 验证JWT
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # 检查数据库中的会话
            query = """
            SELECT expires_at FROM sessions 
            WHERE token = ? AND user_id = ?
            """
            
            result = self.db.execute(query, (token, user_id))
            if not result:
                return None
            
            expires_at = datetime.datetime.fromisoformat(result[0][0])
            if expires_at < datetime.datetime.now():
                # 会话已过期
                self._clean_expired_sessions()
                return None
            
            return user_id
            
        except jwt.ExpiredSignatureError:
            # JWT已过期
            return None
        except jwt.InvalidTokenError:
            # 无效令牌
            return None
    
    def refresh_session(self, token):
        """刷新会话"""
        user_id = self.verify_session(token)
        if not user_id:
            return None
        
        # 创建新会话
        new_token, expires_at = self.create_session(user_id)
        
        # 删除旧会话
        self.db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        
        return new_token, expires_at
    
    def _generate_jwt_token(self, user_id):
        """生成JWT令牌"""
        import jwt
        import datetime
        
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _clean_expired_sessions(self):
        """清理过期会话"""
        from datetime import datetime
        
        query = "DELETE FROM sessions WHERE expires_at < ?"
        self.db.execute(query, (datetime.now().isoformat(),))
```

## 2. VPN隧道详细设计

### 2.1 TLS隧道模块

#### 2.1.1 TLSTunnel 类设计
```python
class TLSTunnel:
    def __init__(self, host, port, cert_file, key_file):
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.server = None
        self.clients = {}
    
    def start(self):
        """启动TLS服务器"""
        import ssl
        import socket
        import threading
        
        # 创建SSL上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        context.verify_mode = ssl.CERT_NONE  # 客户端不需要证书
        
        # 创建套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(100)
        
        # 包装为SSL套接字
        self.server = context.wrap_socket(sock, server_side=True)
        
        print(f"TLS隧道服务器启动在 {self.host}:{self.port}")
        
        # 接受连接
        while True:
            try:
                client_sock, addr = self.server.accept()
                print(f"新连接来自: {addr}")
                
                # 在新线程中处理客户端
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                print(f"接受连接错误: {e}")
    
    def _handle_client(self, client_sock, addr):
        """处理客户端连接"""
        import struct
        import json
        
        try:
            # 读取认证信息
            auth_data = self._read_auth_data(client_sock)
            if not auth_data:
                client_sock.close()
                return
            
            # 验证用户
            user_id = self._authenticate_user(auth_data)
            if not user_id:
                client_sock.close()
                return
            
            print(f"用户 {user_id} 认证成功")
            
            # 处理隧道数据
            self._handle_tunnel_data(client_sock, user_id, addr)
            
        except Exception as e:
            print(f"处理客户端错误: {e}")
        finally:
            client_sock.close()
            if addr in self.clients:
                del self.clients[addr]
    
    def _read_auth_data(self, client_sock):
        """读取认证数据"""
        import struct
        
        # 读取数据长度
        length_bytes = client_sock.recv(4)
        if len(length_bytes) < 4:
            return None
        
        data_length = struct.unpack('!I', length_bytes)[0]
        
        # 读取数据
        data = b''
        while len(data) < data_length:
            chunk = client_sock.recv(min(4096, data_length - len(data)))
            if not chunk:
                return None
            data += chunk
        
        # 解析JSON
        import json
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return None
    
    def _authenticate_user(self, auth_data):
        """验证用户"""
        token = auth_data.get('token')
        if not token:
            return None
        
        # 使用SessionManager验证令牌
        session_mgr = SessionManager.get_instance()
        return session_mgr.verify_session(token)
    
    def _handle_tunnel_data(self, client_sock, user_id, addr):
        """处理隧道数据"""
        import struct
        import select
        
        self.clients[addr] = {
            'sock': client_sock,
            'user_id': user_id,
            'last_active': time.time()
        }
        
        while True:
            # 检查连接是否活跃
            if time.time() - self.clients[addr]['last_active'] > 300:  # 5分钟超时
                break
            
            # 使用select检查可读性
            readable, _, _ = select.select([client_sock], [], [], 1.0)
            if not readable:
                continue
            
            try:
                # 读取数据包类型
                packet_type = client_sock.recv(1)
                if not packet_type:
                    break
                
                # 处理不同类型的数据包
                if packet_type == b'\x01':  # 数据包
                    self._handle_data_packet(client_sock, user_id)
                elif packet_type == b'\x02':  # 心跳包
                    self._handle_heartbeat(client_sock, addr)
                elif packet_type == b'\x03':  # 控制包
                    self._handle_control_packet(client_sock, user