from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.timezone import now
from django.http import JsonResponse
from loguru import logger
import json
import hashlib

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

def Response(message:str, method:str):
    response = JsonResponse({'message': message})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = method
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response



def signin(request):
    '''
    登录
    '''
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['name']
        password = data['password']

        # 验证登录
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request=request, user=user)
            request.session['usertype'] = user.last_name

            logger.success(f'{user.username}登录')
            response = Response(message='Success', method='POST')
            return response
        else:
            logger.error(f'{user.username}登录失败')
            response = Response(message='PASSWORD ERROR', method='POST')
            return response

def auto_login(request):
    '''
    验证sessionid后自动登录
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            user = get_user_from_sessionid(sessionid=sessionid)
            if session.expire_date > timezone.now():
                # 验证sessionid合法后返回登录成功
                logger.success(f'{user.username}自动登录成功')
                return JsonResponse({'message': 'Success'}, status=200)
            else:
                logger.success(f'{user.username}session失效，需重新登录')
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

from SMS.views import verify_code, send_verification_email
def forget_password_send_code(request):
    '''
    忘记密码界面发送sms_code
    '''
    email = json.loads(request.body)['email']
    return send_verification_email(email)


def forget_password(request):
    '''
    忘记密码后重置密码
    '''
    data = json.loads(request.body)
    email = data['email']
    code = data['code']
    status = verify_code(email, code)
    if status == True:
        # 验证通过
        try:
            new_password = data['new_password']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            logger(f'{user.username}修改密码成功')

            return JsonResponse({'message': '密码修改成功'})

        except User.DoesNotExist:
            return JsonResponse({'message': '该账号未注册'}, status=200)
    else:
        return status
