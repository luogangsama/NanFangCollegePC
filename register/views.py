from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from common.models import UserProfile
import json
import hashlib
# Create your views here.

def Response(message:str, method:str):
    response = JsonResponse({'message': message})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = method
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

from SMS.views import send_verification_email, verify_code
def register_send_code(request):
    '''
    注册时向邮箱发送验证码
    '''
    send_verification_email(request)


def register(request):
    '''
    注册
    '''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data['name']
            password = data['password']
            email = data['email']
            
            # 判断验证码是否有效
            verify_code(request)

            try:
                user = User.objects.get(username=username)
                response = Response(message='Existed', method='POST')
                return response
            except:
                record = User.objects.create(
                    username=username,
                    last_name='customer',
                    email=email
                )
                UserProfile.objects.create(
                    user=record, # 在用户信息表中初始化一行
                    phoneNumber='None'
                )
                record.set_password(password)
                record.save()
                response = Response(message='Success', method='POST')
                return response

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Method not allowed'}, status=405)