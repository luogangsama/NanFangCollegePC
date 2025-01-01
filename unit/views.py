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


# Create your views here.
def get_user_from_sessionid(sessionid):
    try:
        # 获取会话对象
        session = Session.objects.get(session_key=sessionid)

        # 检查会话是否过期
        if session.expire_date < now():
            return None  # 会话已过期

        # 获取会话数据
        session_data = session.get_decoded()

        # 提取用户 ID
        user_id = session_data.get('_auth_user_id')

        # 返回用户对象
        return User.objects.get(pk=user_id) if user_id else None
    except Session.DoesNotExist:
        return None  # sessionid 无效
    except User.DoesNotExist:
        return None  # 用户不存在

def user_get_city_and_weather(request):
    '''
    获取用户存储的IP
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                IP = cache.get(f'{user.username}_ip')
                while IP is None:
                    logger.success(f'未存储{user.username}的IP信息，开始尝试获取')
                    save_ip(user.username, json.loads(request.body)['ip'])
                    IP = cache.get(f'{user.username}_ip')

                # 部分使用流量的用户获取的地址和adcode是空列表
                # 因为缓存机制会导致空列表也储存一段时间，下次连
                # 接wifi后访问此网页也会直接返回空列表。为避免这
                # 种情况，额外给此用户一次获取地址的机会
                if len(IP['adcode']) == 0 or len(IP['city']) == 0:
                    logger.warning(f'再次存储{user.username}的IP信息')
                    save_ip(user.username, json.loads(request.body)['ip'])
                if len(IP['adcode']) == 0 or len(IP['city']) == 0:
                    JsonResponse({'message': 'Unable obtain location info'}, status=200)

                logger.success(f'成功从缓存中获取{user.username}的IP信息: \n{IP}')
                city = IP['city']
                adcode = IP['adcode']
                weather = get_weather(adcode)
                return JsonResponse({
                    'message': 'Success',
                    'IP': {
                        'city': city,
                    },
                    'weather': weather
                })
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)
    
def save_ip(username, ip):
    '''
    存储用户的IP，有效时间30分钟
    '''
    apiKey = '7be7dff3729983328f5bbc4815cd5022'
    get_adcode_from_ip_url = f'https://restapi.amap.com/v3/ip?ip={ip}&key={apiKey}'
    response = requests.get(get_adcode_from_ip_url)
    city = response.json()['city']
    adcode = response.json()['adcode']
    cache.set(
        f'{username}_ip',
        {
            'city': city,
            'adcode': adcode
        },
        1800)

def save_weather(adcode):
    '''
    暂存一段时间某地某时刻的天气，有效时间为高德天气api最近一次更新时间开始15分钟
    '''
    apiKey = '7be7dff3729983328f5bbc4815cd5022'
    url = f'https://restapi.amap.com/v3/weather/weatherInfo?key={apiKey}&city={adcode}&extensions=base'

    response = requests.get(url)
    weather_info = response.json()['lives'][0]

    # 储存数据
    cache.set(
        f'{adcode}_weather',
        {
            'temperature': weather_info['temperature'], # 温度
            'weather': weather_info['weather'], # 天气
            'humidity': weather_info['humidity'], # 湿度
            'winddirection': weather_info['winddirection'], # 风向
            'windpower': weather_info['windpower'], # 风力
            'updateTime': weather_info['reporttime'] # 更新时间
        },
        900
        )

def get_weather(adcode):
    '''
    根据adcode读取先前储存在缓存中的天气信息
    '''
    weather = cache.get(f'{adcode}_weather')
    while weather is None:
        logger.success(f'未储存{adcode}的天气信息，开始尝试获取')
        save_weather(adcode)
        weather = cache.get(f'{adcode}_weather')
    logger.success(f'{adcode}的天气信息获取成功:\n{weather}')
    # 结构如下
    # weather = {
    #     'temperature': temperature,
    #     'weather': weather,
    #     'humidity': humidity,
    #     'winddirection': winddirection,
    #     'windpower': windpower,
    #     'updateTime': updateTime
    # }
    return {'weather': weather}