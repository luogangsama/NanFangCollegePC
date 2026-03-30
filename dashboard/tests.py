from django.test import TestCase, Client
from django.contrib.auth.models import User
from common.models import UserProfile, call_report_table, OrderAssignment
import json


class MultiWorkerAssignmentTestCase(TestCase):
    """
    多人员订单分配功能测试用例
    """

    def setUp(self):
        """
        设置测试数据
        """
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            identity='admin',
            phoneNumber='13800000001',
            dutyTime='1'
        )
        
        self.worker1 = User.objects.create_user(
            username='worker1',
            password='worker123',
            email='worker1@test.com'
        )
        UserProfile.objects.create(
            user=self.worker1,
            identity='worker',
            phoneNumber='13800000002',
            dutyTime='1'
        )
        
        self.worker2 = User.objects.create_user(
            username='worker2',
            password='worker123',
            email='worker2@test.com'
        )
        UserProfile.objects.create(
            user=self.worker2,
            identity='worker',
            phoneNumber='13800000003',
            dutyTime='1'
        )
        
        self.worker3 = User.objects.create_user(
            username='worker3',
            password='worker123',
            email='worker3@test.com'
        )
        UserProfile.objects.create(
            user=self.worker3,
            identity='worker',
            phoneNumber='13800000004',
            dutyTime='1'
        )
        
        self.customer = User.objects.create_user(
            username='customer1',
            password='customer123',
            email='customer@test.com'
        )
        UserProfile.objects.create(
            user=self.customer,
            identity='customer',
            phoneNumber='13800000005'
        )
        
        self.report = call_report_table.objects.create(
            user=self.customer,
            userPhoneNumber='13800000005',
            address='测试地址',
            issue='测试问题',
            date='2025-03-27 10:00',
            weekday='1',
            call_date='2025-03-26 15:00',
            status='0'
        )
        
        self.client.login(username='admin_test', password='admin123')

    def test_single_worker_assignment(self):
        """
        测试单人员分配（向后兼容）
        """
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerName': 'worker1'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Success')
        self.assertIn('data', data)
        self.assertEqual(data['data']['assignedWorkers'], ['worker1'])
        
        assignments = OrderAssignment.objects.filter(report=self.report, status='active')
        self.assertEqual(assignments.count(), 1)
        self.assertEqual(assignments.first().worker.username, 'worker1')

    def test_multi_worker_assignment(self):
        """
        测试多人员分配
        """
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2', 'worker3']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['assignedWorkers'], ['worker1', 'worker2', 'worker3'])
        
        assignments = OrderAssignment.objects.filter(report=self.report, status='active')
        self.assertEqual(assignments.count(), 3)

    def test_max_workers_exceeded(self):
        """
        测试超过最大人数限制
        """
        worker4 = User.objects.create_user(username='worker4', password='worker123')
        UserProfile.objects.create(user=worker4, identity='worker', phoneNumber='13800000006')
        
        worker5 = User.objects.create_user(username='worker5', password='worker123')
        UserProfile.objects.create(user=worker5, identity='worker', phoneNumber='13800000007')
        
        worker6 = User.objects.create_user(username='worker6', password='worker123')
        UserProfile.objects.create(user=worker6, identity='worker', phoneNumber='13800000008')
        
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2', 'worker3', 'worker4', 'worker5', 'worker6']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Max workers exceeded')
        self.assertEqual(data['error']['code'], 'MAX_WORKERS_EXCEEDED')

    def test_invalid_worker(self):
        """
        测试无效维修人员
        """
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['non_existent_worker']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Invalid worker')
        self.assertEqual(data['error']['code'], 'INVALID_WORKER')

    def test_duplicate_assignment(self):
        """
        测试重复分配
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1']
            }),
            content_type='application/json'
        )
        
        report2 = call_report_table.objects.create(
            user=self.customer,
            userPhoneNumber='13800000005',
            address='测试地址2',
            issue='测试问题2',
            date='2025-03-27 11:00',
            weekday='1',
            call_date='2025-03-26 16:00',
            status='0'
        )
        
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': report2.id,
                'workerNames': ['worker1']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': report2.id,
                'workerNames': ['worker1']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['message'], 'Duplicate assignment')

    def test_permission_denied(self):
        """
        测试权限不足
        """
        self.client.logout()
        self.client.login(username='customer1', password='customer123')
        
        response = self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)

    def test_get_report_with_multi_workers(self):
        """
        测试获取订单列表包含多人员信息
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2']
            }),
            content_type='application/json'
        )
        
        response = self.client.get('/api/dashboard/get_report_of_same_day/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Success')
        
        reports = data['reports']
        target_report = next((r for r in reports if r['reportId'] == self.report.id), None)
        self.assertIsNotNone(target_report)
        self.assertIn('workerNames', target_report)
        self.assertIn('worker1', target_report['workerNames'])
        self.assertIn('worker2', target_report['workerNames'])

    def test_get_workers_with_assignments(self):
        """
        测试获取维修人员列表包含当前订单数
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1']
            }),
            content_type='application/json'
        )
        
        response = self.client.get('/api/dashboard/today_workers/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Success')
        
        workers = data['workers']
        worker1_data = next((w for w in workers if w['username'] == 'worker1'), None)
        self.assertIsNotNone(worker1_data)
        self.assertIn('currentAssignments', worker1_data)
        self.assertEqual(worker1_data['currentAssignments'], 1)

    def test_worker_get_report_list_with_multi_assignment(self):
        """
        测试维修人员获取历史订单（多人员分配场景）
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2']
            }),
            content_type='application/json'
        )
        
        self.client.logout()
        self.client.login(username='worker1', password='worker123')
        
        response = self.client.get('/api/dashboard/worker_get_report_list/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Success')
        
        report_ids = [r['reportId'] for r in data['report_info']]
        self.assertIn(self.report.id, report_ids)
        
        self.client.logout()
        self.client.login(username='worker2', password='worker123')
        
        response = self.client.get('/api/dashboard/worker_get_report_list/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        report_ids = [r['reportId'] for r in data['report_info']]
        self.assertIn(self.report.id, report_ids)

    def test_complete_report_updates_assignment_status(self):
        """
        测试结单时更新 OrderAssignment 状态
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2']
            }),
            content_type='application/json'
        )
        
        self.client.logout()
        self.client.login(username='customer1', password='customer123')
        
        response = self.client.post(
            '/api/dashboard/complete_report/',
            data=json.dumps({
                'reportId': self.report.id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        active_assignments = OrderAssignment.objects.filter(
            report=self.report,
            status='active'
        )
        self.assertEqual(active_assignments.count(), 0)
        
        completed_assignments = OrderAssignment.objects.filter(
            report=self.report,
            status='completed'
        )
        self.assertEqual(completed_assignments.count(), 2)

    def test_cancel_report_updates_assignment_status(self):
        """
        测试取消订单时更新 OrderAssignment 状态
        """
        self.client.post(
            '/api/dashboard/assign_order/',
            data=json.dumps({
                'reportId': self.report.id,
                'workerNames': ['worker1', 'worker2']
            }),
            content_type='application/json'
        )
        
        self.client.logout()
        self.client.login(username='customer1', password='customer123')
        
        response = self.client.post(
            '/api/dashboard/cancel_report/',
            data=json.dumps({
                'reportId': self.report.id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        active_assignments = OrderAssignment.objects.filter(
            report=self.report,
            status='active'
        )
        self.assertEqual(active_assignments.count(), 0)
        
        cancelled_assignments = OrderAssignment.objects.filter(
            report=self.report,
            status='cancelled'
        )
        self.assertEqual(cancelled_assignments.count(), 2)
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
            identity='worker',
            dutyTime='5',
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

    def test_get_duty_time(self):
        response = self.client.login(username='testuser', password='testpassword')
        logger.info(f'登录结果: {response}')
        response = self.client.get('/api/dashboard/get_duty_time/')
        self.assertEqual(response.status_code, 200)
        response_body = response.json()
        self.assertEqual(response_body['message'], 'Success')
        self.assertEqual(response_body['dutyTime'], '5')
        logger.info(f'获取到的值班时间: {response_body["dutyTime"]}')
