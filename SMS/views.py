from django.shortcuts import render
from django.core.mail import send_mail
from django.core.cache import cache
from django.http import JsonResponse
from NanFangCollegePC.settings import EMAIL_FROM
from loguru import logger
import random
import json

def generate_verification_code(length=6):
    """生成随机验证码"""
    return ''.join(random.choices('0123456789', k=length))

# Create your views here.
def store_verification_code(email, code, timeout=300):
    """将验证码存储到缓存中"""
    cache.set(f"verification_code_{email}", code, timeout)

def send_verification_email(email):
    # 生成验证码
    code = generate_verification_code()
    
    # 存储验证码
    store_verification_code(email, code)
    
    # 发送邮件
    subject = '广州南方学院PC志愿者服务队'
    message = f'您的验证码是：{code}，有效期为5分钟。'
    try:
        send_mail(subject, message, EMAIL_FROM, [email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f'发送验证码邮件失败: {e}')
        return False

def verify_code(email, input_code) -> bool:
    input_code = input_code.upper()
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