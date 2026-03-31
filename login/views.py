from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from loguru import logger
import re

from utils.validators import validate_password, validate_email
from utils.log_masker import mask_email


# def Response(message:str, method:str):
#     response = JsonResponse({'message': message})
#     response['Access-Control-Allow-Origin'] = '*'
#     response['Access-Control-Allow-Methods'] = method
#     response['Access-Control-Allow-Headers'] = 'Content-Type'
#     return response


class Signin(APIView):
    '''
    登录接口
    '''
    def post(self, request):
        data = request.data
        username = data['name']
        password = data['password']

        # 如果用户名是邮箱格式，先通过邮箱找到对应的用户名，再进行登录验证
        email = r'^([a-zA-Z0-9]+[_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
        if re.match(email, username):
            try:
                user = User.objects.get(email=username)
                username = user.username
            except User.DoesNotExist:
                logger.error(f'{username}登录失败')
                return Response({'message': 'USER NOT EXIST'}, status=status.HTTP_401_UNAUTHORIZED)

        # 验证登录
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request=request, user=user)

            logger.success(f'{user.username}登录')
            return Response({'message': 'Success'}, status=status.HTTP_200_OK)
        else:
            logger.error(f'{username}登录失败')
            return Response({'message': 'USERNAME AND PASSWORD ARE REQUIRED'}, status=status.HTTP_401_UNAUTHORIZED)

class AutoSignin(APIView):
    '''
    自动登录接口
    '''
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)


from SMS.views import verify_code, send_verification_email
class ForgetPasswordSendCode(APIView):
    '''
    忘记密码界面发送sms_code
    '''
    def post(self, request):
        email = request.data.get('email')
        logger.info(f"邮箱: {mask_email(email)}")
        result = send_verification_email(email)
        if result:
            return Response({'message': '验证码已发送'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': '发送失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgetPassword(APIView):
    def post(self, request):
        '''
        忘记密码后重置密码
        已加强安全：密码强度验证、输入验证
        '''
        data = request.data
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')
        
        if not all([email, code, new_password]):
            return Response({'message': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_email(email)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(new_password)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        result = verify_code(email, code)
        if result == True:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()

                logger.success(f'用户修改密码成功')

                return Response({'message': '密码修改成功'}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({'message': '该账号未注册'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return result