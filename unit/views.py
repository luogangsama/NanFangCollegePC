from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from django.core.cache import cache
from django.contrib.auth.models import User
from loguru import logger
import json
import datetime
import requests

def session_check(func):
    def wrapper(request, *args, **kwargs):
        sessionid = request.COOKIES.get('sessionid')
        if not sessionid:
            return JsonResponse({'message': 'No sessionid cookie'}, status=400)
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
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
    '''
    获取用户存储的IP
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    IP = cache.get(f'{user.username}_ip')
    while IP is None:
        logger.success(f'缓存中未存储{user.username}的位置信息，开始尝试通过解析IP地址获取')
        save_ip(user.username, json.loads(request.body)['ip'])
        IP = cache.get(f'{user.username}_ip')

    # 部分使用流量的用户获取的地址和adcode是空列表
    # 因为缓存机制会导致空列表也储存一段时间，下次连
    # 接wifi后访问此网页也会直接返回空列表。为避免这
    # 种情况，额外给此用户一次获取地址的机会
    if len(IP['adcode']) == 0 or len(IP['city']) == 0:
        logger.warning(f'用户{user.username}的位置信息为空，再次尝试解析IP并存储位置信息')
        save_ip(user.username, json.loads(request.body)['ip'])
    if len(IP['adcode']) == 0 or len(IP['city']) == 0:
        logger.error(f'依然无法获取{user.username}的位置信息，强制返回，位置信息于缓存中将储存为空')
        return JsonResponse({'message': 'Unable obtain location info'}, status=500)

    logger.success(f'缓存中成功获取{user.username}的位置信息: {IP}')
    province = IP['province']
    city = IP['city']
    adcode = IP['adcode']
    weather = get_weather(province, city, adcode)
    return JsonResponse({
        'message': 'Success',
        'IP': {
            'city': city,
        },
        'weather': weather
    }, status=200)
    
def save_ip(username, ip):
    '''
    存储用户的IP，有效时间30分钟
    '''
    with open('/root/get_user_ip_info_api_key.txt', 'r') as f:
        apiKey = f.readline()
        apiKey = apiKey[0: -1]
    get_adcode_from_ip_url = f'https://restapi.amap.com/v3/ip?ip={ip}&key={apiKey}'
    response = requests.get(get_adcode_from_ip_url)
    city = response.json()['city']
    province = response.json()['province']
    adcode = response.json()['adcode']
    cache.set(
        f'{username}_ip',
        {
            'province': province,
            'city': city,
            'adcode': adcode
        },
        1800)

def save_weather(province, city, adcode):
    '''
    暂存一段时间某地某时刻的天气，有效时间为高德天气api最近一次更新时间开始15分钟
    '''
    # apiKey = '7be7dff3729983328f5bbc4815cd5022'
    with open('/root/get_weather_key.txt', 'r') as f:
        apiKey = f.readline()
        apiKey = apiKey[0: -1]
    with open('/root/get_weather_id.txt', 'r') as f:
        apiId = f.readline()
        apiId = apiId[0: -1]
    url = f'https://cn.apihz.cn/api/tianqi/tqyb.php?id={apiId}&key={apiKey}&sheng={province}&place={city}'

    response = requests.get(url)
    weather_info = response.json()

    # 储存数据
    cache.set(
        f'{adcode}_weather',
        {
            'temperature': weather_info['temperature'], # 温度
            'weather': weather_info['weather1'], # 天气
            'humidity': weather_info['humidity'], # 湿度
            'winddirection': weather_info['windDirection'], # 风向
            'windpower': weather_info['windSpeed'], # 风力
        },
        900
        )

def get_weather(province, city, adcode):
    '''
    根据adcode读取先前储存在缓存中的天气信息
    '''
    weather = cache.get(f'{adcode}_weather')
    while weather is None:
        logger.success(f'缓存中未储存{city}的天气信息，开始尝试通过adcode向高德获取')
        save_weather(province, city, adcode)
        logger.success(f'从高德成功获取{city}的天气信息，存入缓存')
        weather = cache.get(f'{adcode}_weather')
    logger.success(f'缓存中成功获取{city}的天气信息:\n{weather}')
    # 结构如下
    # weather = {
    #     'temperature': temperature,
    #     'weather': weather,
    #     'humidity': humidity,
    #     'winddirection': winddirection,
    #     'windpower': windpower,
    # }
    return {'weather': weather}
