# VPN 代理隧道项目 - 集成测试设计文档

## 1. 集成测试概述

### 1.1 测试目标
- 验证各模块间的接口和交互
- 测试完整业务流程
- 确保系统整体功能正确性
- 模拟真实使用场景

### 1.2 测试范围
- 认证系统完整流程
- VPN连接建立和维护
- 客户端-服务端通信
- 错误处理和恢复机制

### 1.3 测试环境
- **服务端**: Python 3.8+ on Ubuntu
- **客户端**: Windows模拟 + Android模拟
- **数据库**: SQLite
- **网络**: 本地回环 + 模拟网络环境

## 2. 认证系统集成测试

### 2.1 完整注册流程测试

#### 2.1.1 测试用例设计
```python
import unittest
import tempfile
import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest.mock import patch, MagicMock
from auth.user_manager import UserManager
from auth.code_service import CodeService
from auth.session_manager import SessionManager
from auth.sqlite_db import SQLiteDatabase

class TestFullRegistrationFlow(unittest.TestCase):
    """完整注册流程集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        
        # 初始化组件
        self.db = SQLiteDatabase(self.db_path)
        self.user_manager = UserManager(self.db)
        self.session_mgr = SessionManager(self.db, "test_secret")
        
        self.config = {
            'code_expires': 300,
            'sms_provider': 'console'
        }
        self.code_service = CodeService(self.db, self.config)
        
        # 启动模拟HTTP服务器
        self.server = self._start_mock_server()
    
    def tearDown(self):
        """清理测试环境"""
        self.server.shutdown()
        os.unlink(self.db_path)
    
    def _start_mock_server(self):
        """启动模拟HTTP服务器"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class MockAuthHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/auth/check-user':
                    self._handle_check_user()
                elif self.path == '/api/auth/send-code':
                    self._handle_send_code()
                elif self.path == '/api/auth/register':
                    self._handle_register()
                else:
                    self.send_error(404)
            
            def _handle_check_user(self):
                """处理检查用户请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # 模拟检查逻辑
                exists = self.server.test_db.check_user_exists(
                    data.get('username'),
                    data.get('email'),
                    data.get('phone')
                )
                
                response = {'exists': exists}
                self._send_json_response(200, response)
            
            def _handle_send_code(self):
                """处理发送验证码请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # 模拟发送验证码
                identifier = data.get('identifier')
                code_type = data.get('type', 'register')
                
                try:
                    self.server.test_code_service.send_verification_code(
                        identifier, code_type
                    )
                    response = {'success': True}
                    self._send_json_response(200, response)
                except Exception as e:
                    response = {'success': False, 'error': str(e)}
                    self._send_json_response(400, response)
            
            def _handle_register(self):
                """处理注册请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # 验证验证码
                identifier = data.get('email') or data.get('phone')
                code = data.get('code')
                
                if not self.server.test_code_service.verify_code(
                    identifier, code, 'register'
                ):
                    response = {'success': False, 'error': '验证码错误'}
                    self._send_json_response(400, response)
                    return
                
                # 创建用户
                try:
                    user_id, token = self.server.test_user_manager.create_user(
                        data['username'],
                        data['password'],
                        data.get('email'),
                        data.get('phone')
                    )
                    
                    response = {
                        'success': True,
                        'user_id': user_id,
                        'token': token,
                        'user': {'id': user_id, 'username': data['username']}
                    }
                    self._send_json_response(200, response)
                except Exception as e:
                    response = {'success': False, 'error': str(e)}
                    self._send_json_response(400, response)
            
            def _send_json_response(self, status_code, data):
                """发送JSON响应"""
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            
            def log_message(self, format, *args):
                """禁用日志"""
                pass
        
        # 创建服务器
        server = HTTPServer(('localhost', 8888), MockAuthHandler)
        server.test_db = self.db
        server.test_user_manager = self.user_manager
        server.test_code_service = self.code_service
        
        # 在后台线程中启动服务器
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # 等待服务器启动
        time.sleep(0.5)
        
        return server
    
    def test_complete_registration_flow(self):
        """测试完整注册流程"""
        import requests
        
        # 1. 检查用户是否存在（应该不存在）
        check_response = requests.post(
            'http://localhost:8888/api/auth/check-user',
            json={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'phone': '13800138000'
            }
        )
        self.assertEqual(check_response.status_code, 200)
        self.assertFalse(check_response.json()['exists'])
        
        # 2. 发送验证码
        send_response = requests.post(
            'http://localhost:8888/api/auth/send-code',
            json={
                'identifier': 'newuser@example.com',
                'type': 'register'
            }
        )
        self.assertEqual(send_response.status_code, 200)
        self.assertTrue(send_response.json()['success'])
        
        # 3. 从数据库获取验证码（模拟用户收到）
        query = "SELECT code FROM verification_codes WHERE identifier = ?"
        result = self.db.execute(query, ('newuser@example.com',))
        self.assertEqual(len(result), 1)
        verification_code = result[0][0]
        
        # 4. 提交注册
        register_response = requests.post(
            'http://localhost:8888/api/auth/register',
            json={
                'username': 'newuser',
                'password': 'Test@123456',
                'email': 'newuser@example.com',
                'code': verification_code
            }
        )
        self.assertEqual(register_response.status_code, 200)
        register_data = register_response.json()
        
        # 验证注册结果
        self.assertTrue(register_data['success'])
        self.assertIsNotNone(register_data['token'])
        self.assertEqual(register_data['user']['username'], 'newuser')
        
        # 5. 验证用户已创建
        query = "SELECT username, email FROM users WHERE username = ?"
        result = self.db.execute(query, ('newuser',))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'newuser')
        self.assertEqual(result[0][1], 'newuser@example.com')
    
    def test_registration_with_invalid_code(self):
        """测试使用无效验证码注册"""
        import requests
        
        # 1. 发送验证码
        requests.post(
            'http://localhost:8888/api/auth/send-code',
            json={
                'identifier': 'test@example.com',
                'type': 'register'
            }
        )
        
        # 2. 使用错误验证码注册
        register_response = requests.post(
            'http://localhost:8888/api/auth/register',
            json={
                'username': 'testuser',
                'password': 'Test@123456',
                'email': 'test@example.com',
                'code': '999999'  # 错误验证码
            }
        )
        
        self.assertEqual(register_response.status_code, 400)
        self.assertFalse(register_response.json()['success'])
        self.assertIn('验证码错误', register_response.json()['error'])
    
    def test_registration_duplicate_user(self):
        """测试重复用户注册"""
        import requests
        
        # 1. 创建第一个用户
        requests.post(
            'http://localhost:8888/api/auth/send-code',
            json={'identifier': 'user1@example.com', 'type': 'register'}
        )
        
        # 获取验证码
        query = "SELECT code FROM verification_codes WHERE identifier = ?"
        result = self.db.execute(query, ('user1@example.com',))
        code = result[0][0]
        
        requests.post(
            'http://localhost:8888/api/auth/register',
            json={
                'username': 'user1',
                'password': 'Test@123456',
                'email': 'user1@example.com',
                'code': code
            }
        )
        
        # 2. 尝试用相同信息注册第二个用户
        requests.post(
            'http://localhost:8888/api/auth/send-code',
            json={'identifier': 'user1@example.com', 'type': 'register'}
        )
        
        result = self.db.execute(query, ('user1@example.com',))
        code = result[0][0]
        
        register_response = requests.post(
            'http://localhost:8888/api/auth/register',
            json={
                'username': 'user2',  # 不同用户名，相同邮箱
                'password': 'Test@123456',
                'email': 'user1@example.com',  # 重复邮箱
                'code': code
            }
        )
        
        # 应该失败，因为邮箱已存在
        self.assertEqual(register_response.status_code, 400)
        self.assertFalse(register_response.json()['success'])
```

### 2.2 完整登录流程测试

#### 2.2.1 测试用例设计
```python
class TestFullLoginFlow(unittest.TestCase):
    """完整登录流程集成测试"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db = SQLiteDatabase(self.db_path)
        
        # 初始化组件
        self.user_manager = UserManager(self.db)
        self.session_mgr = SessionManager(self.db, "test_secret")
        
        self.config = {'code_expires': 300, 'sms_provider': 'console'}
        self.code_service = CodeService(self.db, self.config)
        
        # 创建测试用户
        self.test_user_id, self.test_token = self.user_manager.create_user(
            username="testuser",
            password="Test@123456",
            email="test@example.com"
        )
        
        # 启动模拟服务器
        self.server = self._start_mock_server()
    
    def tearDown(self):
        self.server.shutdown()
        os.unlink(self.db_path)
    
    def _start_mock_server(self):
        """启动模拟HTTP服务器（扩展认证处理）"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class MockAuthHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/auth/login':
                    self._handle_login()
                elif self.path == '/api/auth/login-with-code':
                    self._handle_login_with_code()
                elif self.path == '/api/auth/verify-token':
                    self._handle_verify_token()
                else:
                    # 调用父类处理其他路径
                    super().do_POST()
            
            def _handle_login(self):
                """处理密码登录"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # 认证用户
                result = self.server.test_user_manager.authenticate_user(
                    data['username'],
                    data['password']
                )
                
                if result:
                    user_id, token = result
                    response = {
                        'success': True,
                        'token': token,
                        'user': {
                            'id': user_id,
                            'username': data['username']
                        }
                    }
                    self._send_json_response(200, response)
                else:
                    response = {'success': False, 'error': '认证失败'}
                    self._send_json_response(401, response)
            
            def _handle_login_with_code(self):
                """处理验证码登录"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                identifier = data['identifier']
                code = data['code']
                
                # 验证验证码
                if not self.server.test_code_service.verify_code(
                    identifier, code, 'login'
                ):
                    response = {'success': False, 'error': '验证码错误'}
                    self._send_json_response(401, response)
                    return
                
                # 根据标识符查找用户
                query = """
                SELECT id, username FROM users 
                WHERE email = ? OR phone = ? LIMIT 1
                """
                result = self.server.test_db.execute(query, (identifier, identifier))
                
                if not result:
                    response = {'success': False, 'error': '用户不存在'}
                    self._send_json_response(401, response)
                    return
                
                user_id, username = result[0]
                
                # 创建会话
                token, _ = self.server.test_session_mgr.create_session(user_id)
                
                response = {
                    'success': True,
                    'token': token,
                    'user': {'id': user_id, 'username': username}
                }
                self._send_json_response(200, response)
            
            def _handle_verify_token(self):
                """验证令牌"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                token = data['token']
                user_id = self.server.test_session_mgr.verify_session(token)
                
                if user_id:
                    response = {'valid': True, 'user_id': user_id}
                    self._send_json_response(200, response)
                else:
                    response = {'valid': False}
                    self._send_json_response(401, response)
            
            def _send_json_response(self, status_code, data):
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
        
        server = HTTPServer(('localhost', 8889), MockAuthHandler)
        server.test_db = self.db
        server.test_user_manager = self.user_manager
        server.test_session_mgr = self.session_mgr
        server.test_code_service = self.code_service
        
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.5)
        
        return server
    
    def test_password_login_success(self):
        """测试密码登录成功"""
        import requests
        
        response = requests.post(
            'http://localhost:8889/api/auth/login',
            json={
                'username': 'testuser',
                'password': 'Test@123456'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['token'])
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_password_login_wrong_password(self):
        """测试错误密码登录"""
        import requests
        
        response = requests.post(
            'http://localhost:8889/api/auth/login',
            json={
                'username': 'testuser',
                'password': 'WrongPassword'
            }
        )
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['success'])
    
    def test_code_login_success(self):
        """测试验证码登录成功"""
        import requests
        
        # 1. 发送登录验证码
        requests.post(
            'http://localhost:8888/api/auth/send-code',
            json={
                'identifier': 'test@example.com',
                'type': 'login'
            }
        )
        
        # 2. 获取验证码
        query = "SELECT code FROM verification_codes WHERE identifier = ?"
        result = self.db.execute(query, ('test@example.com',))
        code = result[0][0]
        
        # 3. 使用验证码登录
        response = requests.post(
            'http://localhost:8889/api/auth/login-with-code',
            json={
                'identifier': 'test@example.com',
                'code': code
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['token'])
    
    def test_token_verification(self):
        """测试令牌验证"""
        import requests
        
        # 1. 先登录获取令牌
        login_response = requests.post(
            'http://localhost:8889/api/auth/login',
            json={
                'username': 'testuser',
                'password': 'Test@123456'
            }
        )
        token = login_response.json()['token']
        
        # 2. 验证令牌
        verify_response = requests.post(
            'http://localhost:8889/api/auth/verify-token',
            json={'token': token}
        )
        
        self.assertEqual(verify_response.status_code, 200)
        self.assertTrue(