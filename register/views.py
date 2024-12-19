from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
import json
import hashlib
# Create your views here.

from pymysql import connect

conn = connect(
    host='localhost',
    user='root',
    password='py123456',
    database='NanFangCollegePC'
)

def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            name = data['name']
            password = data['password']

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # 避免昵称重复
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users;")
            conn.commit()
            data = cursor.fetchall()
            if data and name in data[0]:
                response = JsonResponse({'message': 'Existed'})

            else:
                cursor.execute(f"INSERT users(name, password) VALUES('{name}', '{hashed_password}')")
                conn.commit()
                response = JsonResponse({'message': 'Success'})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST'
            response['Access-Control-Allow-Headers'] = 'Content-Type'

            cursor.close()

            return response

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

