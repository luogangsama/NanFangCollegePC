from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from common.models import call_report_table
from django.contrib.auth.models import User
import hashlib
import json

# Create your views here.

def get_user_from_sessionid(sessionid):
    try:
        # 获取会话对象
        session = Session.objects.get(session_key=sessionid)

        # 检查会话是否过期
        if session.expire_date < now():
            return None  # 会话已过期

        # 获取会话数据
        session_data = session.get_decoded()

        # 提取用户 ID
        user_id = session_data.get('_auth_user_id')

        # 返回用户对象
        return User.objects.get(pk=user_id) if user_id else None
    except Session.DoesNotExist:
        return None  # sessionid 无效
    except User.DoesNotExist:
        return None  # 用户不存在

def modifyPassword(request):
    pass

def get_weather(request):
    apiKey = '7be7dff3729983328f5bbc4815cd5022'
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                return JsonResponse({'message': 'Success', 'apiKey': apiKey}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def call_report(request):
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)

                data = json.loads(request.body)
                userPhoneNumber = data['userPhoneNumber']
                address = data['address']
                issue = data['issue']
                date = data['date']

                call_report_table.objects.create(
                    username=user.username,
                    userPhoneNumber=userPhoneNumber,
                    address=address,
                    issue=issue,
                    date=date
                )
                return JsonResponse({'message': 'Success', 'orderDetails': '订单提交成功'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def user_get_history_report(request):
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，根据sessionid获取用户
                user = get_user_from_sessionid(sessionid=sessionid)
                
                try:
                    report_info = call_report_table.objects.get(
                        username=user.username
                    )
                except:
                    return JsonResponse({'message': 'No history report'}, status=200)
                # 获取用户历史订单信息
                userPhoneNumber = report_info.userPhoneNumber
                address = report_info.address
                issue = report_info.issue
                allocationState = report_info.allocationState
                completeState = report_info.completeState
                date = report_info.date # 预约时间

                return JsonResponse({
                    'message': 'Success',
                    'report_info': {
                        'userPhoneNumber': userPhoneNumber,
                        'address': address,
                        'issue': issue,
                        'allocationState': allocationState,
                        'date': date
                    }
                }, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)
