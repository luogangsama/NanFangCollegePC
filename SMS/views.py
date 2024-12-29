from django.shortcuts import render
from django.core.mail import send_mail
from django.core.cache import cache
from django.http import JsonResponse
from NanFangCollegePC.settings import EMAIL_FROM
import random
import json

def generate_verification_code(length=6):
    """生成随机验证码"""
    return ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=length))

# Create your views here.
def store_verification_code(email, code, timeout=300):
    """将验证码存储到缓存中"""
    cache.set(f"verification_code_{email}", code, timeout)

def send_verification_email(request):
    email = json.loads(request.body)['email']
    print(email)
    if not email:
        return JsonResponse({'message': '邮箱不能为空'}, status=200)
    
    # 生成验证码
    code = generate_verification_code()
    
    # 存储验证码
    store_verification_code(email, code)
    
    # 发送邮件
    subject = '您的验证码'
    message = f'您的验证码是：{code}，有效期为5分钟。'
    try:
        status = send_mail(subject, message, EMAIL_FROM, [email], fail_silently=False)
        return JsonResponse({'message': '验证码已发送'}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'message': '发送失败'}, status=200)

def verify_code(request) -> bool:
    # email = request.POST.get('email')
    # input_code = request.POST.get('code')
    data = json.loads(request.body)
    email = data['email']
    input_code = data['code']
    
    if not email or not input_code:
        return JsonResponse({'message': '邮箱和验证码不能为空'}, status=200)
    
    # 从缓存中获取验证码
    stored_code = cache.get(f"verification_code_{email}")
    if stored_code is None:
        return JsonResponse({'message': '验证码已过期'}, status=200)
    
    if stored_code != input_code:
        return JsonResponse({'message': '验证码错误'}, status=200)
    
    # 验证成功返回True
    return True
    
