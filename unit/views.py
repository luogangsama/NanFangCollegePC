if __name__ != '__main__':
    from django.contrib.sessions.models import Session
    from django.http import JsonResponse, HttpResponse
    from django.utils import timezone
    from django.core.cache import cache
    from django.contrib.auth.models import User
    from common.models import locationWeather

from loguru import logger
from datetime import timedelta
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
@logger.catch
def get_user_from_sessionid(sessionid):
    # 获取会话对象
    session = Session.objects.get(session_key=sessionid)
    # 获取会话数据
    session_data = session.get_decoded()
    # 提取用户 ID
    user_id = session_data.get('_auth_user_id')
    # 返回用户对象
    return User.objects.get(pk=user_id) if user_id else None


def _get_ip_location(ip: str) -> dict:
    """
    根据IP地址获取地理位置信息
    使用新的IP地理位置API: https://api.gznfpc.cn/api/v1/
    
    Args:
        ip: IP地址，支持IPv4/IPv6
        
    Returns:
        dict: 包含province和city的字典
    """
    get_ip_location_url = f'https://api.gznfpc.cn/api/v1/?ip={ip}'
    default = {
        'province': '广东省',
        'city': '广州市'
    }
    try:
        response = requests.get(get_ip_location_url, timeout=5).json()
        # 新API响应格式:
        # {
        #   "code": 0,
        #   "message": "success",
        #   "data": {
        #     "ip": "8.8.8.8",
        #     "country": "美国",
        #     "province": "加利福尼亚",
        #     "city": "芒廷维尤",
        #     "isp": "Google LLC",
        #     "country_code": "US",
        #     "is_china": false,
        #     "ip_version": 4
        #   }
        # }

        if response.get('code') != 0:
            logger.error(f"IP查询API返回错误: {response.get('message')}")
            return default
            
        data = response.get('data', {})
        province = data.get('province', '')
        city = data.get('city', '')
        
        if not province or not city:
            logger.warning(f"IP查询结果缺少省份或城市信息: {data}")
            return default
            
        return {
            'province': province,
            'city': city
        }
    except requests.exceptions.Timeout:
        logger.error('IP地理位置查询请求超时')
        return default
    except requests.exceptions.RequestException as e:
        logger.error(f'IP地理位置查询请求异常: {e}')
        return default
    except Exception as e:
        logger.opt(exception=True).error(f'{e}')
        return default


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
            logger.opt(exception=True).error(f'{e}')
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

@logger.catch
@session_check
def userWeather(request):
    try:
        EXPIRES_TIME = 15 #分钟

        '''获取用户属地'''
        user = get_user_from_sessionid(request.COOKIES.get('sessionid'))
        userLocation = user.profile.location
        logger.info(f'从数据库中获取到{user.username}的属地: {userLocation}')

        if not userLocation or timezone.now() > user.profile.locationExpiresAt + timedelta(minutes=EXPIRES_TIME):
            # 用户属地过期或者为空就调用第三方接口进行定位
            userIP = _get_client_ip(request)
            logger.info(f'{user.username}的IP: [ {userIP} ]')
            logger.info(f'开始尝试获取{user.username}的属地信息')
            userLocation = _get_ip_location(ip=userIP)
            if userLocation == None:
                logger.warning(f'无法获取用户位置信息，异常IP: [ {userIP} ]')
                return JsonResponse({'message': '无法获取用户位置信息，请检查网络连接'}, status=403)
            user.profile.location = userLocation
            user.profile.locationExpiresAt = timezone.now() + timedelta(minutes=EXPIRES_TIME)
            user.profile.save()
            logger.success(f'{user.username}的属地: {userLocation["province"]}-{userLocation["city"]}，入库成功')
        
        '''获取属地的天气信息'''
        logger.info(f'开始尝试从数据库中获取{userLocation}的天气')
        weather = locationWeather.objects.filter(location=userLocation)
        weatherInfo = None
        if not weather or timezone.now() > weather[0].expiresAt + timedelta(minutes=EXPIRES_TIME):
            logger.info(f'数据库中无{userLocation}天气信息或已过期，开始尝试重新获取')
            # 如果数据库中没有该用户的天气信息或已过期，则从第三方API获取并更新数据库
            province, city = userLocation['province'], userLocation['city']
            apiId, apiKey = _get_weather_api_id_and_key()
            utc_now = timezone.now()
            now = timezone.localtime(utc_now).strftime('%Y-%m-%d %H:%M:%S')

            weatherInfo = _get_weather(
                apiId=apiId,
                apiKey=apiKey,
                province=province,
                city=city
            )
            if weatherInfo['code'] != 200:
                logger.error(f'获取天气失败，属地{province}-{city}')
                return JsonResponse({'message': '无法获取天气信息，请检查网络连接'}, status=403)
            
            weatherInfo = {
                'temperature': weatherInfo['nowinfo']['temperature'], # 温度
                'weather': weatherInfo['weather1'], # 天气
                'humidity': weatherInfo['nowinfo']['humidity'], # 湿度
                'winddirection': weatherInfo['nowinfo']['windDirection'], # 风向
                'windpower': weatherInfo['nowinfo']['windSpeed'], # 风力
                'updateTime': now
            }
            if weather:
                '''不为空时更新'''
                weather[0].weather = weatherInfo
                weather[0].expiresAt = timezone.now() + timedelta(minutes=EXPIRES_TIME)
                weather[0].save()
            else:
                '''为空时创建'''
                locationWeather.objects.create(
                    location=userLocation,
                    weather=weatherInfo,
                    expiresAt=timezone.now() + timedelta(minutes=EXPIRES_TIME)
                )
            logger.success(f'{userLocation}天气:{weatherInfo}，入库成功')
        else:
            weatherInfo = weather[0].weather
            logger.success(f'数据库中成功获取{userLocation}的天气: {weatherInfo}')
        
        return JsonResponse({
            'message': 'Success',
            'IP': {
                'city': userLocation['city']
            },
            'weather': {
                'weather': weatherInfo
                }
            },
            status=200)

    except Exception as e:
        logger.opt(exception=True).error(f'{e}')
        return JsonResponse({'message': '天气业务异常'}, status=500)


if __name__ == '__main__':
    import requests

    ip = '120.197.18.205'
    location = _get_ip_location(ip=ip)
    province, city = location['province'], location['city']
    apiId, getWeatherKey = _get_weather_api_id_and_key('/home/luoenhao/Documents')
    weather_info = _get_weather(apiId=apiId, apiKey=getWeatherKey, province=province, city=city)
    test = {
                'temperature': weather_info['nowinfo']['temperature'], # 温度
                'weather': weather_info['weather1'], # 天气
                'humidity': weather_info['nowinfo']['humidity'], # 湿度
                'winddirection': weather_info['nowinfo']['windDirection'], # 风向
                'windpower': weather_info['nowinfo']['windSpeed'], # 风力
            }
    print(weather_info)
    print(test)