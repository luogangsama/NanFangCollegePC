from django.test import TestCase
from loguru import logger

# Create your tests here.

class Unit_Tests(TestCase):
    def test_get_csrf_token(self):
        response = self.client.get('/api/unit/csrf/')
        logger.info(f"Response: {response.json()}")
        logger.info(f"CSRF Token: {response.cookies.get('csrftoken')}")
        self.assertEqual(response.status_code, 200)