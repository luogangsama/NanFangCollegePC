if __name__ != '__main__':
    from django.contrib.sessions.models import Session
    from django.http import JsonResponse, HttpResponse
    from django.utils import timezone
    from django.core.cache import cache
    from django.contrib.auth.models import User

from loguru import logger
import requests
import hashlib
import json
import os
import base64
import uuid

def session_check(func):
    '''
    验证用户是否以登录状态发起请求
    '''
    def wrapper(request, *args, **kwargs):
        sessionid = request.COOKIES.get('sessionid')
        if not sessionid:
            return JsonResponse({'message': 'No sessionid cookie'}, status=400)
        try:
            session = Session.objects.get(session_key=sessionid)
            # session_data = session.get_decoded()
            if session.expire_date <= timezone.now():
                return JsonResponse({'message': 'Session has expired'}, status=401)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=401)
        return func(request, *args, **kwargs)
    return wrapper


# Create your views here.
def get_user_from_sessionid(sessionid):
    # 获取会话对象
    session = Session.objects.get(session_key=sessionid)
    # 获取会话数据
    session_data = session.get_decoded()
    # 提取用户 ID
    user_id = session_data.get('_auth_user_id')
    # 返回用户对象
    return User.objects.get(pk=user_id) if user_id else None

@session_check
def user_get_city_and_weather(request):
    try:
        '''
        获取用户存储的IP
        '''
        sessionid = request.COOKIES.get('sessionid')
        user = get_user_from_sessionid(sessionid=sessionid)
        IP = cache.get(f'{user.username}_ip')
        while IP is None:
            logger.success(f'缓存中未存储{user.username}的位置信息，开始尝试通过解析IP地址获取')
            # save_ip(user.username, json.loads(request.body)['ip'])
            save_ip(user.username, _get_client_ip(request=request))
            IP = cache.get(f'{user.username}_ip')

        # 部分使用流量的用户获取的地址是空列表
        # 因为缓存机制会导致空列表也储存一段时间，下次连
        # 接wifi后访问此网页也会直接返回空列表。为避免这
        # 种情况，额外给此用户一次获取地址的机会
        if len(IP['province']) == 0 or len(IP['city']) == 0:
            logger.warning(f'用户{user.username}的位置信息为空，再次尝试解析IP并存储位置信息')
            # save_ip(user.username, json.loads(request.body)['ip'])
            ip = _get_client_ip(request)
            save_ip(user.username, ip)
        if len(IP['province']) == 0 or len(IP['city']) == 0:
            logger.error(f'依然无法获取{user.username}的位置信息，强制返回，位置信息于缓存中将储存为空；错误IP：[ {ip} ]')
            return JsonResponse({'message': 'Unable obtain location info'}, status=500)

        logger.success(f'缓存中成功获取{user.username}的位置信息: {IP}')
        province = IP['province']
        city = IP['city']
        weather = get_weather(province, city)
        return JsonResponse({
            'message': 'Success',
            'IP': {
                'city': city,
            },
            'weather': weather
        }, status=200)

    except Exception as e:
        logger.error(f'{e}')


def _get_ip_location(ip: str)->tuple[str, str]:
    get_ip_location_url = f'https://api.vore.top/api/IPv4?v4={ip}'
    response = requests.get(get_ip_location_url).json()
    try:
        if response['msg'] != 'SUCCESS':
            raise KeyError("查询IP属地接口响应异常，请检查接口状态")
        elif response['ipdata']['info1'] == '保留IP':
            raise KeyError('')

        # 根据观察，当info3为空串时获取的是国内属地信息，info1/info2分别对应省/市
        # 否则获取的是国外属地信息，info1/info2/info3分别对应国/省/市
        if response['ipdata']['info3'] == '':
            province = response['ipdata']['info1']
            city = response['ipdata']['info2']
        else:
            province = response['ipdata']['info2']
            city = response['ipdata']['info3']
        return province, city
    except KeyError as e:
        # 接口异常是打印日志且将返回值均设置为空串
        logger.error(f'{e}')
        return '', ''
    except Exception as e:
        logger.error(f'{e}')
        return '', ''

    
def save_ip(username, ip):
    '''
    存储用户的IP，有效时间30分钟
    '''
    province, city = _get_ip_location(ip=ip)
    cache.set(
        f'{username}_ip',
        {
            'province': province,
            'city': city,
        },
        1800)

def _get_weather_api_id_and_key(dir: str='/root')->tuple[str, str]:
    '''
    获取通过请求获取当地天气时需携带的apiId与apiKey
    '''
    with open(f'{dir}/get_weather_id.txt', 'r') as f:
        apiId = f.readline()[0: -1]
    with open(f'{dir}/get_weather_key.txt', 'r') as f:
        apiKey = f.readline()[0: -1]

    return apiId, apiKey

def _get_weather(apiId:str, apiKey:str, province:str, city:str)->dict:
    '''
    根据参数发起请求以获取天气信息
    '''
    url = f'https://cn.apihz.cn/api/tianqi/tqyb.php?id={apiId}&key={apiKey}&sheng={province}&place={city}'
    response = requests.get(url).json()
    weather_info = response

    return weather_info



def save_weather(province, city):
    '''
    暂存一段时间某地某时刻的天气，有效时间为高德天气api最近一次更新时间开始15分钟
    '''
    apiId, apiKey = _get_weather_api_id_and_key()
    utc_now = timezone.now()
    now = timezone.localtime(utc_now).strftime('%Y-%m-%d %H:%M:%S')

    weather_info = _get_weather(
        apiId=apiId,
        apiKey=apiKey,
        province=province,
        city=city
    )
    # 储存数据
    try:
        cache.set(
            f'{province}_{city}_weather',
            {
                'temperature': weather_info['nowinfo']['temperature'], # 温度
                'weather': weather_info['weather1'], # 天气
                'humidity': weather_info['nowinfo']['humidity'], # 湿度
                'winddirection': weather_info['nowinfo']['windDirection'], # 风向
                'windpower': weather_info['nowinfo']['windSpeed'], # 风力
                'updateTime': now
            },
            900
            )
    except KeyError:
        raise("第三方天气接口返回的天气信息结构发生变化，请检查接口状态")

def get_weather(province, city):
    '''
    根据省份与城市读取先前储存在缓存中的天气信息
    '''
    weather = cache.get(f'{province}_{city}_weather')
    while weather is None:
        logger.success(f'缓存中未储存{city}的天气信息，开始尝试通过province,city获取天气')
        save_weather(province, city)
        logger.success(f'成功获取{city}的天气信息，存入缓存')
        weather = cache.get(f'{province}_{city}_weather')
    logger.success(f'缓存中成功获取{province}_{city}的天气信息:\n{weather}')
    # 结构如下
    # weather = {
    #     'temperature': temperature,
    #     'weather': weather,
    #     'humidity': humidity,
    #     'winddirection': winddirection,
    #     'windpower': windpower,
    #     'updateTime': now
    # }
    return {'weather': weather}

def _get_client_ip(request):
    """
    获取客户端的真实IP地址
    """
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR'))
        if ip == 'localhost' or ip == '127.0.0.1':
            raise KeyError("获取到用户ip为本机回环地址，请留意nginx等反向代理的配置")
    except KeyError as e:
        logger.error(f'{e}')
    return ip

def validMessageFromWeiXin(func):
    '''
    验证消息是否来自微信服务器
    params:
        func: 被装饰函数
    returns:
        bool: 是否合法
    '''
    def wrapper(request, *args, **kwargs):
        try:
            token_path = '/root/weixin_token.txt'
            with open(token_path, 'r') as f:
                '''
                weixin_token.txt中的内容为微信公众号开放平台中手动配置的值
                '''
                token = f.readline()
                token = token[0:-1]
        except Exception as e:
            logger.error(e)
            token = ''
        # 获取请求参数
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        signature = request.GET.get('signature', '')
        echostr = request.GET.get('echostr', '')

        # 计算签名
        originalStrList = [token, timestamp, nonce]
        originalStrList.sort()
        originalStr = ''.join(originalStrList)
        sign = hashlib.sha1(originalStr.encode('utf-8')).hexdigest()

        # 判断签名是否一致
        if sign != signature:
            logger.error(f'非法来源，请求参数为: {request.GET}')
            HttpResponse("Forbidden")
        else: 
            if echostr:
                logger.success(f'合法来源，请求参数为: {request.GET}')
                return HttpResponse(echostr)
            else:
                return func(request, *args, **kwargs)

    return wrapper


def getAccessToken(AppID:str, AppSecret:str):
    '''
    获取微信公众号accessToken
    GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET 
    '''
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={AppID}&secret={AppSecret}'
    response = requests.get(url)
    print(response.text)
    accessToken = json.loads(response.text)['access_token']
    return accessToken

class ImageConverter:
    '''
    Base64图片转换工具
    '''
    @staticmethod
    def imageToBase64(path):
        '''
        图片转Base64字符串
        '''
        try:
            with open(path, 'rb') as f:
                base64Data = base64.b64encode(f.read()).decode("utf-8")
                return base64Data
        except Exception as e:
            raise Exception(f'图片转Base64失败: {str(e)}')
        
    @staticmethod
    def base64ToImage(base64Str, outputPath=None, fileName=None):
        try:
            if ',' in base64Str:
                base64Str = base64Str.split(',')[1]

            # 解码Base64为图片
            image = base64.b64decode(base64Str)
            outputPath = outputPath or os.path.join(os.path, 'message_board/images')
            os.makedirs(outputPath, exist_ok=True)

            if not fileName:
                fileName = f'{uuid.uuid4().hex}.jpg'
            
            outputPath = os.path.join(outputPath, fileName)

            with open(outputPath, 'wb') as f:
                f.write(image)
            
            return outputPath
        
        except Exception as e:
            raise Exception(f'Base64转图片失败: {str(e)}')

if __name__ == '__main__':
    import requests

    ip = '120.197.18.205'
    province, city = _get_ip_location(ip=ip)
    apiId, getWeatherKey = _get_weather_api_id_and_key('/home/luoenhao/Documents')
    print(_get_weather(apiId=apiId, apiKey=getWeatherKey, province=province, city=city))