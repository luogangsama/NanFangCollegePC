from django.shortcuts import render
from django.contrib.auth.models import User
from pymysql import connect
import json

# Create your views here.

conn = connect(
    host='localhost',
    user='root',
    password='py123456',
    database='NanFangCollegePC'
)

def Response(message:str, method:str):
    response = JsonResponse({'message': message})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = method
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def user_set_session_view(request, username):
    # 假设前端传递了用户名
    user = User.objects.filter(username=username).first()
    
    if user:
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        return JsonResponse({'message': 'Session created successfully'})
    else:
        return JsonResponse({'message': 'User not found'}, status=404)

def login(request):
    if request.method == 'POST':
        try:
            data = json.load(request.body)
            name = data['name']
            password = data['password']
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            cursor = conn.cursor()
            cursor.execute(f"SELECT id, name, password FROM users WHERE name='{name};'")
            conn.commit()
            # 返回查询的信息
            user_id, user_name, return_password = cursor.fetchone()
            # 判断用户是否存在
            if return_password is None:
                response = Response('USER NOT EXIST')
                return response

            # 判断密码是否正确
            elif return_password == hashed_password:
                # 验证成功，设置会话
                request.session["user_id"] = user_id
                request.session["name"] = user_name
                response = Response('Success', 'POST')
                return response

            elif return_password != hashed_password:
                response = Response('PASSWORD ERROR', 'POST')
                return response
            
            else:
                response = Response('UNKNOWN ERROR', 'POST')
                return response

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
        
        finally:
            cursor.close()
