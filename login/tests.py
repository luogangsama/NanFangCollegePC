from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from loguru import logger

# Create your tests here.

class LoginTestCase(TestCase):
    def setUp(self):
        # 在每个测试方法执行前运行，设置测试环境
        self.user = User.objects.create_user(username='testuser', password='testpassword', email="2332893844@qq.com")
    def test_signin_success(self):
        # 测试登录接口
        response = self.client.post('/api/users/login/', {'name': 'testuser', 'password': 'testpassword'}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_signin_failure(self):
        # 测试登录失败的情况
        response = self.client.post('/api/users/login/', {'name': 'testuser', 'password': 'wrongpassword'}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signin_user_not_exist(self):
        # 测试用户不存在的情况
        response = self.client.post('/api/users/login/', {'name': 'nonexistentuser', 'password': 'testpassword'}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auto_signin(self):
        # 测试自动登录接口
        # logger.info(self.client.post('/api/users/login/', {'name': 'testuser', 'password': 'testpassword'}, content_type='application/json'))
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/api/users/validate-session/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forget_password_send_code(self):
        # 测试忘记密码发送验证码接口
        logger.info(self.client.post('/api/users/forget_password_send_code/', {'email': User.objects.get(username="testuser").email}, content_type='application/json'))
        code = input("请输入邮箱验证码：")
        self.client.post('/api/users/forget_password', {'email': User.objects.get(username="testuser").email, 'code': code, 'new_password': 'newpassword'}, content_type='application/json')
        result = self.client.login(username='testuser', password='newpassword')

        self.assertEqual(result, True)