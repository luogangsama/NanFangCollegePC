"""
请求频率限制中间件
防止暴力破解、DoS攻击和资源滥用
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from loguru import logger
import time


class RateLimitMiddleware(MiddlewareMixin):
    """
    请求频率限制中间件
    
    基于IP地址或用户ID进行请求频率限制
    """
    
    DEFAULT_RATE_LIMIT = 100
    DEFAULT_WINDOW = 60
    EXEMPT_PATHS = [
        '/api/unit/csrf/',
        '/static/',
        '/favicon.ico',
    ]
    
    PATH_RATE_LIMITS = {
        '/api/users/login/': {'limit': 10, 'window': 60},
        '/api/users/register/': {'limit': 5, 'window': 60},
        '/api/users/register_send_code/': {'limit': 3, 'window': 60},
        '/api/users/forget_password/': {'limit': 5, 'window': 60},
        '/api/users/forget_password_send_code/': {'limit': 3, 'window': 60},
        '/api/dashboard/call_report/': {'limit': 10, 'window': 60},
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def _get_client_identifier(self, request):
        """
        获取客户端唯一标识
        
        Args:
            request: Django请求对象
            
        Returns:
            str: 客户端标识
        """
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', 'unknown'))
        
        return f"ip_{ip}"
    
    def _get_rate_limit_config(self, path):
        """
        获取路径对应的频率限制配置
        
        Args:
            path: 请求路径
            
        Returns:
            dict: 频率限制配置
        """
        config = self.PATH_RATE_LIMITS.get(path)
        if config:
            return config
        return {'limit': self.DEFAULT_RATE_LIMIT, 'window': self.DEFAULT_WINDOW}
    
    def _is_exempt(self, path):
        """
        检查路径是否豁免频率限制
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否豁免
        """
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def process_request(self, request):
        """
        处理请求前的频率限制检查
        
        Args:
            request: Django请求对象
            
        Returns:
            JsonResponse or None
        """
        if self._is_exempt(request.path):
            return None
        
        if request.method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return None
        
        client_id = self._get_client_identifier(request)
        config = self._get_rate_limit_config(request.path)
        
        cache_key = f"rate_limit_{client_id}_{request.path}"
        
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        request_times = cache.get(cache_key, [])
        request_times = [t for t in request_times if t > window_start]
        
        if len(request_times) >= config['limit']:
            logger.warning(
                f'请求频率超限: client={client_id}, path={request.path}, '
                f'count={len(request_times)}, limit={config["limit"]}'
            )
            return JsonResponse({
                'message': '请求过于频繁，请稍后再试',
                'retry_after': config['window']
            }, status=429)
        
        request_times.append(current_time)
        cache.set(cache_key, request_times, config['window'])
        
        return None


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    暴力破解防护中间件
    
    针对登录等敏感接口的额外保护
    """
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = 900
    
    PROTECTED_PATHS = [
        '/api/users/login/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def _get_client_ip(self, request):
        """
        获取客户端IP
        
        Args:
            request: Django请求对象
            
        Returns:
            str: 客户端IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', 'unknown'))
    
    def _is_protected_path(self, path):
        """
        检查是否是受保护的路径
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否受保护
        """
        for protected_path in self.PROTECTED_PATHS:
            if path.startswith(protected_path):
                return True
        return False
    
    def process_request(self, request):
        """
        处理请求前的暴力破解检查
        
        Args:
            request: Django请求对象
            
        Returns:
            JsonResponse or None
        """
        if not self._is_protected_path(request.path):
            return None
        
        if request.method != 'POST':
            return None
        
        client_ip = self._get_client_ip(request)
        lockout_key = f"login_lockout_{client_ip}"
        attempts_key = f"login_attempts_{client_ip}"
        
        if cache.get(lockout_key):
            logger.warning(f'账户锁定中: ip={client_ip}')
            return JsonResponse({
                'message': '账户已被锁定，请15分钟后再试'
            }, status=429)
        
        return None
    
    def process_response(self, request, response):
        """
        处理响应后的暴力破解记录
        
        Args:
            request: Django请求对象
            response: Django响应对象
            
        Returns:
            Django响应对象
        """
        if not self._is_protected_path(request.path):
            return response
        
        if request.method != 'POST':
            return response
        
        client_ip = self._get_client_ip(request)
        attempts_key = f"login_attempts_{client_ip}"
        lockout_key = f"login_lockout_{client_ip}"
        
        if response.status_code == 401:
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, 300)
            
            if attempts >= self.MAX_LOGIN_ATTEMPTS:
                cache.set(lockout_key, True, self.LOCKOUT_TIME)
                cache.delete(attempts_key)
                logger.warning(
                    f'登录失败次数过多，账户已锁定: ip={client_ip}, attempts={attempts}'
                )
        elif response.status_code == 200:
            cache.delete(attempts_key)
        
        return response
