from django.shortcuts import render
from django.http import JsonResponse

from unit.views import session_check
from common.models import report_message_board_record, call_report_table
import json
# Create your views here.

@session_check
def get_message_record(requests):
    data = json.loads(requests.body)
    reportId = int(data['reportId'])
    # 根据订单号获取订单对象
    report = call_report_table.objects.get(id=reportId)
    # 根据订单对象查找留言记录表，获取属于此订单的留言记录
    message_records = report_message_board_record.objects.all().order_by('-pk').filter(
        report=report
    )
    # 构建响应消息结构
    return_message_record = {
        'message': 'Success',
        'message_record': []
    }
    for message_record in message_records:
        # 遍历留言记录并将其填入响应消息
        username = message_record.user.username
        message = message_record.message
        date = message_record.date

        return_message_record['message_record'].append(
            {
                'username': username,
                'message': message,
                'date': date
            }
        )
    return JsonResponse(return_message_record)