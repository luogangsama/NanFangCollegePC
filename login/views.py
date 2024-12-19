from django.shortcuts import render
from pymysql import connect
import json

# Create your views here.

conn = connect(
    host='localhost',
    user='root',
    password='py123456',
    database='NanFangCollegePC'
)

def login(request):
    if request.method == 'POST':
        try:
            data = json.load(request.body)
            name = data['name']
            password = data['password']

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
