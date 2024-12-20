from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
import hashlib

# Create your views here.

def Response(message:str, method:str):
    response = JsonResponse({'message': message})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = method
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response



def signin(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['name']
        password = data['password']

        # 验证登录
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request=request, user=user)
            request.session['usertype'] = user.last_name

            response = Response(message='Success', method='POST')
            return response
        else:
            response = Response(message='PASSWORD ERROR', method='POST')
            return response