from django.shortcuts import render
from django.http import JsonResponse
from django.utils.html import escape

from unit.views import session_check
from common.models import report_message_board_record, call_report_table, User, OrderAssignment
from django.db.models import Q
import json
# Create your views here.

@session_check
def get_message_record(requests):
    data = json.loads(requests.body)
    reportId = int(data['reportId'])
    report = call_report_table.objects.get(id=reportId)
    message_records = report_message_board_record.objects.all().order_by('pk').filter(
        report=report
    )
    return_message_record = {
        'message': 'Success',
        'message_record': []
    }
    for message_record in message_records:
        username = escape(message_record.user.username)
        message = escape(message_record.message)
        date = message_record.date

        return_message_record['message_record'].append(
            {
                'username': username,
                'message': message,
                'date': date
            }
        )
    return JsonResponse(return_message_record)

@session_check
def get_message_list(requests):
    """
    获取用户相关的订单列表
    支持多人员分配：通过 OrderAssignment 表查询维修人员相关的订单
    """
    body = json.loads(requests.body)
    userId = body['userId']
    user = User.objects.get(id=userId)
    
    assignment_report_ids = OrderAssignment.objects.filter(
        worker=user,
        status='active'
    ).values_list('report_id', flat=True)
    
    report_infos = call_report_table.objects.all().order_by('-pk').filter(
        Q(id__in=assignment_report_ids) | Q(user=user)
    )
    
    return_report_info = {
        'message': 'Success',
        'report_info': []
    }
    for report_info in report_infos:
        issue = report_info.issue
        status = report_info.status
        date = report_info.date
        report_id = report_info.id

        return_report_info['report_info'].append({
            'reportId': report_id,
            'issue': issue,
            'status': status,
            'date': date,
        })
    return JsonResponse(return_report_info, status=200)

