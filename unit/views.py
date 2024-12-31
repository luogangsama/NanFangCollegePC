from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from django.core.cache import cache
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

def user_get_ip(request):
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
                if IP is None:
                    return JsonResponse({'message': 'No IP'})
                city = IP['city']
                adcode = IP['adcode']
                return JsonResponse({
                    'message': 'Success',
                    'IP': {
                        'city': city,
                        'adcode': adcode
                    }
                })
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)
    
def user_save_ip(request):
    '''
    存储用户的IP，有效时间30分钟
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                city = json.loads(request.body)['city']
                adcode = json.loads(request.body['adcode'])
                cache.set(
                    f'{user.username}_ip',
                    {
                        'city': city,
                        'adcode': adcode
                    },
                    1800)
                return JsonResponse({'message': 'Success'})
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def save_weather(adcode):
    '''
    暂存一段时间某地某时刻的天气，有效时间为高德天气api最近一次更新时间开始15分钟
    '''
    apiKey = '7be7dff3729983328f5bbc4815cd5022'
    url = f'https://restapi.amap.com/v3/weather/weatherInfo?key={apiKey}&city={adcode}&extensions=base'

    response = requests.get(url)
    weather_info = response.json()['lives'][0]

    # 获取需要储存的数据
    updateTime = weather_info['reporttime'] # 更新时间
    temperature = weather_info['temperature'] # 温度
    weather = weather_info['weather'] # 天气
    humidity = weather_info['humidity'] # 湿度
    winddirection = weather_info['winddirection'] # 风向
    windpower = weather_info['windpower'] # 风力                

    cache.set(
        f'{adcode}_weather',
        {
            'temperature': temperature,
            'weather': weather,
            'humidity': humidity,
            'winddirection': winddirection,
            'windpower': windpower,
            'updateTime': updateTime
        },
        900
        )

def get_weather(request):
    '''
    根据adcode读取先前储存在缓存中的天气信息
    '''
    sessionid = rq.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容

                adcode = json.loads(request.body)['adcode']

                weather = cache.get(f'{adcode}_weather')
                while weather is None:
                    save_weather(adcode)
                    weather = cache.get(f'{adcode}_weather')
                # 结构如下
                # weather = {
                #     'temperature': temperature,
                #     'weather': weather,
                #     'humidity': humidity,
                #     'winddirection': winddirection,
                #     'windpower': windpower,
                #     'updateTime': updateTime
                # }
                return JsonResponse({
                    'message': 'Success',
                    'weather': weather
                    })
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)