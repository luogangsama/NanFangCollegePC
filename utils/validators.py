"""
输入验证工具模块
提供统一的输入验证函数，防止恶意输入
"""
import re
from django.core.exceptions import ValidationError
from django.utils.html import escape


def validate_phone(phone):
    """
    验证手机号格式
    
    Args:
        phone: 手机号字符串
        
    Returns:
        str: 验证后的手机号
        
    Raises:
        ValidationError: 手机号格式不正确
    """
    if not phone:
        raise ValidationError("手机号不能为空")
    phone_str = str(phone).strip()
    if not re.match(r'^1[3-9]\d{9}$', phone_str):
        raise ValidationError("手机号格式不正确")
    return phone_str


def validate_password(password):
    """
    验证密码强度
    
    Args:
        password: 密码字符串
        
    Returns:
        str: 验证后的密码
        
    Raises:
        ValidationError: 密码不符合要求
    """
    if not password:
        raise ValidationError("密码不能为空")
    if not isinstance(password, str):
        raise ValidationError("密码必须是字符串")
    if len(password) < 8:
        raise ValidationError("密码长度至少8位")
    if len(password) > 128:
        raise ValidationError("密码长度不能超过128位")
    if not re.search(r'[A-Za-z]', password):
        raise ValidationError("密码需包含字母")
    if not re.search(r'\d', password):
        raise ValidationError("密码需包含数字")
    return password


def validate_username(username):
    """
    验证用户名
    
    Args:
        username: 用户名字符串
        
    Returns:
        str: 验证后的用户名
        
    Raises:
        ValidationError: 用户名不符合要求
    """
    if not username:
        raise ValidationError("用户名不能为空")
    username_str = str(username).strip()
    if len(username_str) < 2 or len(username_str) > 30:
        raise ValidationError("用户名长度需在2-30个字符之间")
    if not re.match(r'^[\w\u4e00-\u9fa5]+$', username_str):
        raise ValidationError("用户名只能包含字母、数字、下划线和中文")
    return username_str


def validate_email(email):
    """
    验证邮箱格式
    
    Args:
        email: 邮箱字符串
        
    Returns:
        str: 验证后的邮箱
        
    Raises:
        ValidationError: 邮箱格式不正确
    """
    if not email:
        raise ValidationError("邮箱不能为空")
    email_str = str(email).strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email_str):
        raise ValidationError("邮箱格式不正确")
    return email_str


def validate_address(address):
    """
    验证地址
    
    Args:
        address: 地址字符串
        
    Returns:
        str: 验证后的地址
        
    Raises:
        ValidationError: 地址不符合要求
    """
    if not address:
        raise ValidationError("地址不能为空")
    address_str = str(address).strip()
    if len(address_str) > 200:
        raise ValidationError("地址长度不能超过200个字符")
    return escape(address_str)


def validate_issue(issue):
    """
    验证问题描述
    
    Args:
        issue: 问题描述字符串
        
    Returns:
        str: 验证后的问题描述
        
    Raises:
        ValidationError: 问题描述不符合要求
    """
    if not issue:
        raise ValidationError("问题描述不能为空")
    issue_str = str(issue).strip()
    if len(issue_str) > 500:
        raise ValidationError("问题描述不能超过500个字符")
    return escape(issue_str)


def validate_report_id(report_id):
    """
    验证订单ID
    
    Args:
        report_id: 订单ID
        
    Returns:
        int: 验证后的订单ID
        
    Raises:
        ValidationError: 订单ID无效
    """
    if not report_id:
        raise ValidationError("订单ID不能为空")
    try:
        report_id_int = int(report_id)
        if report_id_int <= 0:
            raise ValidationError("订单ID无效")
        return report_id_int
    except (ValueError, TypeError):
        raise ValidationError("订单ID格式不正确")


def validate_rating(rating):
    """
    验证评分
    
    Args:
        rating: 评分值
        
    Returns:
        int: 验证后的评分
        
    Raises:
        ValidationError: 评分无效
    """
    if rating is None:
        raise ValidationError("评分不能为空")
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValidationError("评分必须在1-5之间")
        return rating_int
    except (ValueError, TypeError):
        raise ValidationError("评分格式不正确")


def validate_comment(comment):
    """
    验证评价内容
    
    Args:
        comment: 评价内容字符串
        
    Returns:
        str: 验证后的评价内容
        
    Raises:
        ValidationError: 评价内容不符合要求
    """
    if comment is None:
        return ""
    comment_str = str(comment).strip()
    if len(comment_str) > 200:
        raise ValidationError("评价内容不能超过200个字符")
    return escape(comment_str)


def sanitize_input(text, max_length=1000):
    """
    通用输入清理函数
    
    Args:
        text: 输入文本
        max_length: 最大长度限制
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    text_str = str(text).strip()
    if len(text_str) > max_length:
        text_str = text_str[:max_length]
    return escape(text_str)


def validate_required_fields(data, required_fields):
    """
    验证必填字段
    
    Args:
        data: 数据字典
        required_fields: 必填字段列表
        
    Returns:
        dict: 验证后的数据
        
    Raises:
        ValidationError: 缺少必填字段
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"缺少必填字段: {', '.join(missing_fields)}")
    
    return data
