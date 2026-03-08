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
import re
from unit.views import session_check, get_user_from_sessionid


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

        # 如果用户名是邮箱格式，先通过邮箱找到对应的用户名，再进行登录验证
        email = r'^([a-zA-Z0-9]+[_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
        if re.match(email, username):
            try:
                user = User.objects.get(email=username)
                username = user.username
            except User.DoesNotExist:
                logger.error(f'{username}登录失败')
                response = Response(message='USER NOT EXIST', method='POST')
                return response

        # 验证登录
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request=request, user=user)

            logger.success(f'{user.username}登录')
            response = Response(message='Success', method='POST')
            return response
        else:
            logger.error(f'{username}登录失败')
            response = Response(message='PASSWORD ERROR', method='POST')
            return response

@session_check
def auto_login(request):
    '''
    验证sessionid后自动登录
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid)
    # 验证sessionid合法后返回登录成功
    logger.success(f'{user.username}自动登录成功')
    return JsonResponse({'message': 'Success'}, status=200)

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

            logger.success(f'{user.username}修改密码成功')

            return JsonResponse({'message': '密码修改成功'})

        except User.DoesNotExist:
            return JsonResponse({'message': '该账号未注册'}, status=400)
    else:
        return JsonResponse({'message': '验证码失效'}, status=400)
