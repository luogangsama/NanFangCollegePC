from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.utils import timezone
from pymysql import connect
import hashlib

# Create your views here.

conn = connect(
    host='localhost',
    user='root',
    password='py123456',
    database='NanFangCollegePC'
)

def modifyPassword(request):
    pass

def get_weather(request):
    apiKey = '7be7dff3729983328f5bbc4815cd5022'
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                return JsonResponse({'message': 'Success', 'apiKey': apiKey}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)