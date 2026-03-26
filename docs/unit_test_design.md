# VPN 代理隧道项目 - 单元测试设计文档

## 1. 测试概述

### 1.1 测试目标
- 确保各模块功能正确性
- 验证边界条件和异常处理
- 保证代码质量和可维护性
- 为重构和优化提供安全保障

### 1.2 测试原则
- **独立性**: 每个测试用例独立运行
- **可重复性**: 测试结果稳定可重复
- **全面性**: 覆盖正常、边界、异常情况
- **快速性**: 测试执行速度快

### 1.3 测试工具
- **Python**: unittest + pytest
- **Android**: JUnit + Espresso
- **覆盖率**: coverage.py
- **Mock**: unittest.mock

## 2. 认证模块单元测试

### 2.1 UserManager 测试

#### 2.1.1 测试类设计
```python
import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from auth.user_manager import UserManager
from auth.sqlite_db import SQLiteDatabase

class TestUserManager(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 创建数据库实例
        self.db = SQLiteDatabase(self.db_path)
        self.user_manager = UserManager(self.db)
    
    def tearDown(self):
        """测试后清理"""
        os.unlink(self.db_path)
    
    def test_check_user_exists_new_user(self):
        """测试检查新用户是否存在"""
        # 新用户应该不存在
        exists = self.user_manager.check_user_exists(
            username="newuser",
            email="new@example.com",
            phone="13800138000"
        )
        self.assertFalse(exists)
    
    def test_check_user_exists_existing_user(self):
        """测试检查已存在用户"""
        # 先创建用户
        self.user_manager.create_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )
        
        # 检查应该存在
        exists = self.user_manager.check_user_exists(
            username="testuser",
            email="test@example.com"
        )
        self.assertTrue(exists)
    
    def test_create_user_success(self):
        """测试成功创建用户"""
        user_id, token = self.user_manager.create_user(
            username="testuser",
            password="Test@123456",
            email="test@example.com"
        )
        
        self.assertIsNotNone(user_id)
        self.assertIsNotNone(token)
        self.assertGreater(user_id, 0)
    
    def test_create_user_duplicate_username(self):
        """测试创建重复用户名"""
        # 第一次创建
        self.user_manager.create_user(
            username="testuser",
            password="password123"
        )
        
        # 第二次创建应该失败
        with self.assertRaises(Exception):
            self.user_manager.create_user(
                username="testuser",
                password="password456"
            )
    
    def test_authenticate_user_success(self):
        """测试用户认证成功"""
        # 创建用户
        user_id, _ = self.user_manager.create_user(
            username="testuser",
            password="Test@123456"
        )
        
        # 认证
        result = self.user_manager.authenticate_user(
            username="testuser",
            password="Test@123456"
        )
        
        self.assertIsNotNone(result)
        returned_id, token = result
        self.assertEqual(returned_id, user_id)
        self.assertIsNotNone(token)
    
    def test_authenticate_user_wrong_password(self):
        """测试错误密码认证"""
        # 创建用户
        self.user_manager.create_user(
            username="testuser",
            password="correct_password"
        )
        
        # 使用错误密码
        result = self.user_manager.authenticate_user(
            username="testuser",
            password="wrong_password"
        )
        
        self.assertIsNone(result)
    
    def test_authenticate_user_nonexistent(self):
        """测试不存在的用户认证"""
        result = self.user_manager.authenticate_user(
            username="nonexistent",
            password="anypassword"
        )
        
        self.assertIsNone(result)
    
    @patch('auth.user_manager.bcrypt.gensalt')
    @patch('auth.user_manager.bcrypt.hashpw')
    def test_password_hashing(self, mock_hashpw, mock_gensalt):
        """测试密码哈希"""
        # 模拟bcrypt
        mock_gensalt.return_value = b'$2b$12$testsalt'
        mock_hashpw.return_value = b'hashed_password'
        
        password = "Test@123456"
        hashed = self.user_manager._hash_password(password)
        
        mock_gensalt.assert_called_once_with(rounds=12)
        mock_hashpw.assert_called_once_with(
            password.encode(),
            b'$2b$12$testsalt'
        )
        self.assertEqual(hashed, 'hashed_password')
    
    def test_generate_token_structure(self):
        """测试令牌生成结构"""
        import jwt
        
        user_id = 123
        token = self.user_manager._generate_token(user_id)
        
        # 验证令牌结构
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50)
        
        # 可以解码（需要正确的密钥）
        # decoded = jwt.decode(token, options={"verify_signature": False})
        # self.assertEqual(decoded['user_id'], user_id)
```

#### 2.1.2 边界条件测试
```python
class TestUserManagerBoundary(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = SQLiteDatabase(self.temp_db.name)
        self.user_manager = UserManager(self.db)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_username_length_boundary(self):
        """测试用户名长度边界"""
        # 最小长度
        user_id, _ = self.user_manager.create_user(
            username="ab",  # 2字符
            password="Test@123"
        )
        self.assertGreater(user_id, 0)
        
        # 最大长度（假设50字符）
        long_username = "a" * 50
        user_id, _ = self.user_manager.create_user(
            username=long_username,
            password="Test@123"
        )
        self.assertGreater(user_id, 0)
    
    def test_password_complexity(self):
        """测试密码复杂度"""
        # 简单密码应该被拒绝
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty"
        ]
        
        for password in weak_passwords:
            with self.assertRaises(ValueError):
                self.user_manager.create_user(
                    username=f"user_{password}",
                    password=password
                )
    
    def test_email_format_validation(self):
        """测试邮箱格式验证"""
        invalid_emails = [
            "invalid",
            "invalid@",
            "@example.com",
            "invalid@example",
            "invalid@.com"
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValueError):
                self.user_manager.create_user(
                    username=f"user_{email}",
                    password="Test@123456",
                    email=email
                )
    
    def test_phone_format_validation(self):
        """测试手机号格式验证"""
        invalid_phones = [
            "123",
            "1234567890",
            "abcdefghij",
            "1380013800a"
        ]
        
        for phone in invalid_phones:
            with self.assertRaises(ValueError):
                self.user_manager.create_user(
                    username=f"user_{phone}",
                    password="Test@123456",
                    phone=phone
                )
```

### 2.2 CodeService 测试

#### 2.2.1 测试类设计
```python
import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from auth.code_service import CodeService
from auth.sqlite_db import SQLiteDatabase

class TestCodeService(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = SQLiteDatabase(self.temp_db.name)
        
        self.config = {
            'code_expires': 300,  # 5分钟
            'sms_provider': 'console',
            'email_from': 'test@example.com',
            'smtp_host': 'localhost',
            'smtp_port': 587,
            'email_user': 'user',
            'email_password': 'pass'
        }
        
        self.code_service = CodeService(self.db, self.config)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_generate_code_format(self):
        """测试验证码格式"""
        code = self.code_service._generate_code()
        
        # 应该是6位数字
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_generate_code_randomness(self):
        """测试验证码随机性"""
        codes = set()
        for _ in range(100):
            codes.add(self.code_service._generate_code())
        
        # 100次生成应该有足够的随机性
        self.assertGreater(len(codes), 90)
    
    def test_store_code(self):
        """测试存储验证码"""
        identifier = "test@example.com"
        code = "123456"
        code_type = "register"
        
        self.code_service._store_code(identifier, code, code_type)
        
        # 验证存储
        query = """
        SELECT identifier, code, type FROM verification_codes 
        WHERE identifier = ? AND code = ? AND type = ?
        """
        result = self.db.execute(query, (identifier, code, code_type))
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], identifier)
        self.assertEqual(result[0][1], code)
        self.assertEqual(result[0][2], code_type)
    
    def test_verify_code_success(self):
        """测试验证码验证成功"""
        identifier = "test@example.com"
        code = "123456"
        code_type = "register"
        
        # 存储验证码
        self.code_service._store_code(identifier, code, code_type)
        
        # 验证
        result = self.code_service.verify_code(identifier, code, code_type)
        self.assertTrue(result)
        
        # 验证后应该标记为已使用
        query = "SELECT used FROM verification_codes WHERE code = ?"
        result = self.db.execute(query, (code,))
        self.assertEqual(result[0][0], 1)
    
    def test_verify_code_wrong_code(self):
        """测试错误验证码"""
        identifier = "test@example.com"
        code = "123456"
        code_type = "register"
        
        # 存储验证码
        self.code_service._store_code(identifier, code, code_type)
        
        # 使用错误验证码
        result = self.code_service.verify_code(identifier, "999999", code_type)
        self.assertFalse(result)
    
    def test_verify_code_expired(self):
        """测试过期验证码"""
        identifier = "test@example.com"
        code = "123456"
        code_type = "register"
        
        # 手动插入过期验证码
        expired_time = datetime.now() - timedelta(seconds=600)  # 10分钟前
        query = """
        INSERT INTO verification_codes (identifier, code, type, expires_at)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute_insert(query, (
            identifier, code, code_type, expired_time.isoformat()
        ))
        
        # 验证应该失败
        result = self.code_service.verify_code(identifier, code, code_type)
        self.assertFalse(result)
    
    @patch('auth.code_service.smtplib.SMTP')
    def test_send_email_code_success(self, mock_smtp):
        """测试发送邮箱验证码成功"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        email = "test@example.com"
        code = "123456"
        code_type = "register"
        
        self.code_service._send_email_code(email, code, code_type)
        
        # 验证SMTP调用
        mock_smtp.assert_called_once_with('localhost', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('user', 'pass')
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('auth.code_service.smtplib.SMTP')
    def test_send_email_code_failure(self, mock_smtp):
        """测试发送邮箱验证码失败"""
        mock_smtp.side_effect = Exception("SMTP error")
        
        email = "test@example.com"
        code = "123456"
        code_type = "register"
        
        # 应该不会抛出异常，而是回退到控制台输出
        try:
            self.code_service._send_email_code(email, code, code_type)
        except Exception:
            self.fail("send_email_code should handle SMTP errors gracefully")
    
    @patch('auth.code_service.print')
    def test_send_sms_code_console(self, mock_print):
        """测试控制台模式发送短信验证码"""
        phone = "13800138000"
        code = "123456"
        code_type = "register"
        
        self.code_service._send_sms_code(phone, code, code_type)
        
        # 验证打印输出
        mock_print.assert_called_with(
            f"[DEBUG] SMS验证码发送到 {phone}: {code}"
        )
```

### 2.3 SessionManager 测试

#### 2.3.1 测试类设计
```python
import unittest
import tempfile
import os
import jwt
import datetime
from unittest.mock import Mock, patch
from auth.session_manager import SessionManager
from auth.sqlite_db import SQLiteDatabase

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = SQLiteDatabase(self.temp_db.name)
        self.secret_key = "test_secret_key_123"
        self.session_mgr = SessionManager(self.db, self.secret_key)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_create_session(self):
        """测试创建会话"""
        user_id = 123
        ip_address = "192.168.1.100"
        user_agent = "TestClient/1.0"
        
        token, expires_at = self.session_mgr.create_session(
            user_id, ip_address, user_agent
        )
        
        # 验证返回值
        self.assertIsNotNone(token)
        self.assertIsNotNone(expires_at)
        
        # 验证数据库记录
        query = """
        SELECT user_id, token, ip_address, user_agent 
        FROM sessions WHERE token = ?
        """
        result = self.db.execute(query, (token,))
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], user_id)
        self.assertEqual(result[0][2], ip_address)
        self.assertEqual(result[0][3], user_agent)
    
    def test_verify_session_success(self):
        """测试验证会话成功"""
        user_id = 123
        token, _ = self.session_mgr.create_session(user_id)
        
        verified_id = self.session_mgr.verify_session(token)
        self.assertEqual(verified_id, user_id)
    
    def test_verify_session_expired(self):
        """测试验证过期会话"""
        user_id = 123
        
        # 创建立即过期的令牌
        with patch('auth.session_manager.datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
            mock_expired = datetime.datetime(2024, 1, 1, 11, 0, 0)  # 1小时前
            
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.utcnow.return_value = mock_now
            
            # 生成过期令牌
            payload = {
                'user_id': user_id,
                'exp': mock_expired,
                'iat': mock_expired,
                'type': 'access'
            }
            expired_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            
            # 存储到数据库
            query = """
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (?, ?, ?)
            """
            self.db.execute_insert(query, (user_id, expired_token, mock_expired.isoformat()))
            
            # 验证应该失败
            verified_id = self.session_mgr.verify_session(expired_token)
            self.assertIsNone(verified_id)
    
    def test_verify_session_invalid_token(self):
        """测试验证无效令牌"""
        invalid_tokens = [
            "invalid.token.string",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",  # 使用不同密钥
            ""
        ]
        
        for token in invalid_tokens:
            verified_id = self.session_mgr.verify_session(token)
            self.assertIsNone(verified_id)
    
    def test_refresh_session(self):
        """测试刷新会话"""
        user_id = 123
        old_token, _ = self.session_mgr.create_session(user_id)
        
        # 刷新会话
        new_token, new_expires = self.session_mgr.refresh_session(old_token)
        
        # 验证新令牌
        self.assertIsNotNone(new_token)
        self.assertIsNotNone(new_expires)
