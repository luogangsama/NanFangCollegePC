from django.shortcuts import render
from django.core.mail import send_mail
from django.core.cache import cache
from django.http import JsonResponse
from NanFangCollegePC.settings import EMAIL_FROM
from loguru import logger
import random
import json
import hashlib

MAX_SEND_COUNT = 5
MAX_VERIFY_ATTEMPTS = 5
CODE_TIMEOUT = 300
RATE_LIMIT_WINDOW = 3600

def _get_hashed_key(email: str, prefix: str = "verification_code") -> str:
    """
    生成哈希后的缓存key，防止key可预测
    
    Args:
        email: 邮箱地址
        prefix: key前缀
        
    Returns:
        哈希后的key
    """
    hashed_email = hashlib.sha256(email.encode()).hexdigest()
    return f"{prefix}_{hashed_email}"

def generate_verification_code(length=6):
    """
    生成随机验证码
    
    Args:
        length: 验证码长度
        
    Returns:
        随机验证码字符串
    """
    return ''.join(random.choices('0123456789', k=length))

def store_verification_code(email, code, timeout=CODE_TIMEOUT):
    """
    将验证码存储到缓存中，带频率限制
    
    Args:
        email: 邮箱地址
        code: 验证码
        timeout: 过期时间（秒）
        
    Returns:
        tuple: (success: bool, message: str)
    """
    rate_key = _get_hashed_key(email, "verification_rate")
    send_count = cache.get(rate_key, 0)
    
    if send_count >= MAX_SEND_COUNT:
        logger.warning(f'验证码发送频率超限: {email[:3]}***')
        return False, "发送次数过多，请1小时后再试"
    
    code_key = _get_hashed_key(email, "verification_code")
    cache.set(code_key, code, timeout)
    
    cache.set(rate_key, send_count + 1, RATE_LIMIT_WINDOW)
    
    return True, "Success"

def send_verification_email(email):
    """
    发送验证码邮件
    
    Args:
        email: 目标邮箱地址
        
    Returns:
        bool: 是否发送成功
    """
    if not email or '@' not in email:
        logger.warning('无效的邮箱地址')
        return False
    
    code = generate_verification_code()
    
    success, message = store_verification_code(email, code)
    if not success:
        return False
    
    subject = '广州南方学院PC志愿者服务队'
    message_body = f'您的验证码是：{code}，有效期为5分钟。请勿将验证码告知他人。'
    
    try:
        send_mail(subject, message_body, EMAIL_FROM, [email], fail_silently=False)
        logger.info(f'验证码邮件已发送')
        return True
    except Exception as e:
        logger.error(f'发送验证码邮件失败: {e}')
        return False

def verify_code(email, input_code):
    """
    验证验证码，带尝试次数限制
    
    Args:
        email: 邮箱地址
        input_code: 用户输入的验证码
        
    Returns:
        True 或 JsonResponse(错误响应)
    """
    if not email or not input_code:
        return JsonResponse({'message': '邮箱和验证码不能为空'}, status=400)
    
    input_code = input_code.upper()
    
    code_key = _get_hashed_key(email, "verification_code")
    attempt_key = _get_hashed_key(email, "verification_attempt")
    
    stored_code = cache.get(code_key)
    if stored_code is None:
        return JsonResponse({'message': '验证码已过期，请重新获取'}, status=400)
    
    attempts = cache.get(attempt_key, 0) + 1
    cache.set(attempt_key, attempts, CODE_TIMEOUT)
    
    if attempts > MAX_VERIFY_ATTEMPTS:
        cache.delete(code_key)
        cache.delete(attempt_key)
        logger.warning(f'验证码尝试次数超限: {email[:3]}***')
        return JsonResponse({'message': '尝试次数过多，请重新获取验证码'}, status=400)
    
    if stored_code != input_code:
        return JsonResponse({'message': '验证码错误'}, status=400)
    
    cache.delete(code_key)
    cache.delete(attempt_key)
    
    logger.info('验证码验证成功')
    return True
