"""
日志敏感信息脱敏工具
防止敏感信息泄露到日志文件
"""
import re


def mask_email(email):
    """
    邮箱脱敏
    
    Args:
        email: 邮箱地址
        
    Returns:
        str: 脱敏后的邮箱
    """
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 2:
        masked_name = '***'
    else:
        masked_name = name[:2] + '***'
    return f"{masked_name}@{domain}"


def mask_phone(phone):
    """
    手机号脱敏
    
    Args:
        phone: 手机号
        
    Returns:
        str: 脱敏后的手机号
    """
    if not phone:
        return phone
    phone_str = str(phone)
    if len(phone_str) != 11:
        return '***'
    return f"{phone_str[:3]}****{phone_str[-4:]}"


def mask_username(username):
    """
    用户名脱敏
    
    Args:
        username: 用户名
        
    Returns:
        str: 脱敏后的用户名
    """
    if not username:
        return username
    username_str = str(username)
    if len(username_str) <= 2:
        return '***'
    return f"{username_str[0]}***{username_str[-1]}"


def mask_password(password):
    """
    密码脱敏
    
    Args:
        password: 密码
        
    Returns:
        str: 固定返回 ******
    """
    return "******"


def mask_id_card(id_card):
    """
    身份证号脱敏
    
    Args:
        id_card: 身份证号
        
    Returns:
        str: 脱敏后的身份证号
    """
    if not id_card:
        return id_card
    id_str = str(id_card)
    if len(id_str) < 8:
        return '***'
    return f"{id_str[:4]}********{id_str[-4:]}"


def mask_bank_card(card_number):
    """
    银行卡号脱敏
    
    Args:
        card_number: 银行卡号
        
    Returns:
        str: 脱敏后的银行卡号
    """
    if not card_number:
        return card_number
    card_str = str(card_number)
    if len(card_str) < 8:
        return '***'
    return f"{card_str[:4]}****{card_str[-4:]}"


def mask_ip(ip):
    """
    IP地址脱敏
    
    Args:
        ip: IP地址
        
    Returns:
        str: 脱敏后的IP地址
    """
    if not ip:
        return ip
    parts = ip.split('.')
    if len(parts) != 4:
        return '***'
    return f"{parts[0]}.{parts[1]}.***.{parts[3]}"


def sanitize_log_message(message):
    """
    清理日志消息中的敏感信息
    
    Args:
        message: 原始日志消息
        
    Returns:
        str: 清理后的日志消息
    """
    if not message:
        return message
    
    message = str(message)
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    message = re.sub(email_pattern, lambda m: mask_email(m.group()), message)
    
    phone_pattern = r'1[3-9]\d{9}'
    message = re.sub(phone_pattern, lambda m: mask_phone(m.group()), message)
    
    return message


SENSITIVE_FIELDS = {
    'password': mask_password,
    'pwd': mask_password,
    'new_password': mask_password,
    'old_password': mask_password,
    'email': mask_email,
    'phone': mask_phone,
    'mobile': mask_phone,
    'id_card': mask_id_card,
    'bank_card': mask_bank_card,
    'secret': mask_password,
    'token': mask_password,
    'api_key': mask_password,
    'apikey': mask_password,
}


def mask_sensitive_data(data, fields=None):
    """
    对字典中的敏感字段进行脱敏
    
    Args:
        data: 原始数据字典
        fields: 需要脱敏的字段列表，默认使用内置的敏感字段列表
        
    Returns:
        dict: 脱敏后的数据字典
    """
    if not isinstance(data, dict):
        return data
    
    mask_fields = fields or list(SENSITIVE_FIELDS.keys())
    result = {}
    
    for key, value in data.items():
        if key.lower() in [f.lower() for f in mask_fields]:
            mask_func = SENSITIVE_FIELDS.get(key.lower(), mask_password)
            result[key] = mask_func(value)
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value, fields)
        elif isinstance(value, list):
            result[key] = [
                mask_sensitive_data(item, fields) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result
