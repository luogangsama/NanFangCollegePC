from django.test import TestCase
from loguru import logger
from unit.views import order_broadcast_to_dingtalk

# Create your tests here.

class Unit_Tests(TestCase):
    def test_get_csrf_token(self):
        response = self.client.get('/api/unit/csrf/')
        logger.info(f"Response: {response.json()}")
        logger.info(f"CSRF Token: {response.cookies.get('csrftoken')}")
        self.assertEqual(response.status_code, 200)

    def test_dingTalk_robot_send_message(self):
        '''
        测试钉钉机器人发送消息功能
        '''
        order_broadcast_to_dingtalk("测试消息\n测试消息\n")