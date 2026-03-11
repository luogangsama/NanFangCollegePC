from django.test import TestCase
from django.contrib.auth.models import User
from common.models import UserProfile
from loguru import logger
import time

# Create your tests here.

class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')
        UserProfile.objects.create(
            user=self.user, # 在用户信息表中初始化一行
            phoneNumber='12345678910',
        )

    def test_call_report_submission(self):
        '''
        测试报告提交接口
        '''
        data = {
            'userPhoneNumber': '12345678910',
            'address': '测试地址',
            'issue': '测试问题',
            'notes': '测试',
            'date': '2024-01-01 10:00',
            'call_date': '2024-01-01',
        }
        response = self.client.login(username='testuser', password='testpassword')
        logger.info(f'登录结果: {response}')
        response = self.client.post('/api/dashboard/call_report/', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        time.sleep(2)
        response = self.client.post('/api/dashboard/call_report/', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
