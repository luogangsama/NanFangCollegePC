from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from common.models import call_report_table
from common.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.contrib.auth.hashers import check_password
import hashlib
import json
import datetime


from SMS.views import send_verification_email
from SMS.views import verify_code

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

def get_user_info(request):
    '''
    获取用户信息，验证cookies可用后返回用户名
    
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                user = get_user_from_sessionid(sessionid=sessionid)
                return JsonResponse({
                    'message': 'Success',
                    'username': user.username,
                    'label': user.last_name
                })
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)


def get_weather(request):
    '''
    验证前端请求的cookies可用后响应前端一个api密钥（用于获取天气信息）
    '''
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

def call_report(request):
    '''
    接受前端发送的报单请求，并验证cookies后将订单存入数据库
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)

                data = json.loads(request.body)
                userPhoneNumber = data['userPhoneNumber']
                address = data['address']
                issue = data['issue']
                date = data['date']
                call_date = data['call_date'] # 订单提交的时间

                call_report_table.objects.create(
                    user=user,
                    userPhoneNumber=userPhoneNumber,
                    address=address,
                    issue=issue,
                    date=date,
                    call_date=call_date
                )
                return JsonResponse({'message': 'Success', 'orderDetails': '订单提交成功'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def user_get_history_report(request):
    '''
    响应前端用户所报修的历史订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，根据sessionid获取用户
                user = get_user_from_sessionid(sessionid=sessionid)
                
                report_infos = call_report_table.objects.filter(
                    user=user
                    )
                if len(report_infos) == 0:
                    return JsonResponse({'message': 'No history report'}, status=200)

                return_report_info = {
                    'message': 'Success',
                    'report_info':[]
                }
                # 获取用户历史订单信息
                for report_info in report_infos:
                    userPhoneNumber = report_info.userPhoneNumber
                    address = report_info.address
                    issue = report_info.issue
                    status = report_info.status
                    date = report_info.date # 预约时间
                    call_date = report_info.call_date
                    report_id = report_info.id

                    return_report_info['report_info'].append({
                        'reportId': report_id,
                        'userPhoneNumber': userPhoneNumber,
                        'address': address,
                        'issue': issue,
                        'status': status,
                        'date': date,
                        'call_date': call_date
                    })

                return JsonResponse(return_report_info, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def worker_get_report_list(request):
    '''
    获取维修员的历史订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                reports = []
                my_reports = call_report_table.objects.filter(workerName=get_user_from_sessionid(sessionid=sessionid))
                if len(my_reports) == 0:
                    return JsonResponse({'message': 'No my report'}, status=200)
                for report in my_reports:
                    reports.append({
                        'reportId': report.id,
                        'userPhoneNumber': report.userPhoneNumber,
                        'address': report.address,
                        'issue': report.issue,
                        'status': report.status,
                        'date': report.date,
                        'call_date': report.call_date
                    })
                return JsonResponse({
                    'message': 'Success',
                    'report_info': reports
                }, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def log_out(request):
    '''
    验证前端请求的cookies后，搜索session数据库中符合sessionid的数据行予以删除或使其失效
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                logout(request)
                return JsonResponse({'message': 'Success'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def save_user_info(request):
    '''
    验证sessionid合法后保存接收到的手机号码
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                # 解析请求消息体
                data = json.loads(request.body)
# ==================================================================================
                try:
                    new_name = data['newName']
                except:
                    new_name = get_user_from_sessionid(sessionid=sessionid).username
                try:
                    new_phone_number = data['phoneNumber']
                except:
                    try:
                        new_phone_number = UserProfile.objects.get(
                            user=get_user_from_sessionid(sessionid=sessionid)
                        ).phoneNumber
                    except:
                        new_phone_number = None
                #以上一块代码的目的是为了判断用户是只想改任意一项还是两项都要改。
                #电话号码的部分的基本逻辑：若消息体中没有phoneNumber则先查找一下UserProfile表中是否有这个用户对应的号码，
                #若是有则直接拿出来赋值给new_phone_number，这样更新后号码不变，若是查找不到，就预设一个None
# ==================================================================================
                # 确保新名称未被占用
                try: 
                    # 订正可能出现的新旧名相同的情况，后续应当修改实现，这里是临时打个补丁
                    if new_name == get_user_from_sessionid(sessionid=sessionid).username:
                        raise User.DoesNotExist('new name == old name')
                    # 确保新名称未被占用
                    User.objects.get(username=new_name)
                    return JsonResponse({'message': 'This user is existed'})
                except User.DoesNotExist:
                    # 首先更改auth_user表中的username
                    user = User.objects.get(username=get_user_from_sessionid(sessionid=sessionid).username)
                    user.username = new_name
                    user.save()

                    # 然后根据新user去更改phone number
                    userProfile = UserProfile.objects.get(user=user)
                    userProfile.phoneNumber = new_phone_number
                    userProfile.save()
                # 登出再登入（刷新sessionid）
                logout(request=request)
                login(request=request, user=user)
                
                return JsonResponse({'message': 'Success'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)
    
def get_phone_number(request):
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            if session.expire_date > timezone.now():
                try:
                    user = get_user_from_sessionid(sessionid=sessionid)
                    phoneNumber = UserProfile.objects.get(user=user).phoneNumber
                    if phoneNumber == 'None':
                        return JsonResponse({'message': 'No phone number'}, status=200)
                    return JsonResponse({'message': 'Success', 'phoneNumber': phoneNumber}, status=200)
                except User.DoesNotExist:
                    return JsonResponse({'message': 'No phone number'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def renew_password(request):
    '''
    修改密码
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)

                data = json.loads(request.body)
                old_password = data['old_password']
                new_password = data['new_password']

                if check_password(old_password, user.password):
                    user.set_password(new_password)
                    user.save()
                    logout(request=request)
                    login(request=request, user=user)
                    return JsonResponse({'message': 'Success'}, status=200)
                else:
                    return JsonResponse({'message': 'Password error'}, status=200)

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def assign_order(request):
    '''
    管理员分配订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                if user.last_name != 'admin':
                    # 权限不符合
                    return JsonResponse({'message': 'Permission error'}, status=200)
                data = json.loads(request.body)

                try:
                    worker_name = data['workerName']
                    worker = User.objects.get(username=worker_name)
                    if worker.last_name not in ['worker', 'admin']:
                        # 权限不符合
                        return JsonResponse({'message': 'Permission error'}, status=200)
                except User.DoesNotExist:
                    return JsonResponse({'message': 'This worker is no exist'}, status=200)

                try:
                    report_id = data['reportId']
                    report = call_report_table.objects.get(pk=report_id)
                    if report.allocationState:
                        # 订单已被分配
                        return JsonResponse({'message': 'This report is allocated'}, status=200)
                    # 向订单表中填入相关信息并改变状态
                    report.workerName = worker
                    report.workerPhoneNumber = worker.phoneNumber
                    report.stauts = '1'

                    return JsonResponse({'message': 'Success'}, status=200)
                except:
                    return JsonResponse({'message': 'This report is no exist'}, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def complete_report(request):
    '''
    用户结单
    '''
    sessionid = request.COOKIES.get('sessionid')
    
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                data = json.loads(request.body)
                reportId = data['reportId']

                try:
                    report = call_report_table.objects.get(pk=reportId)
                    if report.status == '1':
                        return JsonResponse({'message': 'This report is completed'}, status=200)
                    
                    report.status = '2'
                    report.save()
                    return JsonResponse({'message': 'Success'}, status=200)
                except:
                    return JsonResponse({'message': 'This report is no exist'}, status=200)

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def cancel_report(request):
    '''
    用户撤销报单
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                data = json.loads(request.body)
                reportId = data['reportId']

                try:
                    report = call_report_table.objects.get(id=reportId)
                    report.status = '3'
                    report.save()
                    return JsonResponse({'message': 'Success'}, status=200)
                except:
                    return JsonResponse({'message': 'This report is no exist'}, status=200)

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def reset_email_send_code(request):
    '''
    更改邮箱时发送验证码
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                old_email = user.email
                # 向用户注册账户时绑定的邮箱发送验证码
                return send_verification_email(old_email)

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)

def reset_email(request):
    '''
    验证邮箱验证码后修改用户的邮箱
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                old_email = user.email
                code = json.loads(request.body)['code']
                status = verify_code(old_email, code)
                if status == True:
                    new_email = json.loads(request.body)['new_email']
                    user.email = new_email
                    user.save()

                    return JsonResponse({'message': 'Success'})
                else:
                    return status

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)


def get_staff_of_same_day(request):
    '''
    获取与分单人员同一天值班的人员名单
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)
                staffs = UserProfile.objects.filter(
                    dutyTime=UserProfile.objects.get(user=user).dutyTime
                )
                return_data = {
                    'message': 'Success',
                    'workers': []
                    }

                for staff in staffs:
                    return_data['workers'].append({'username': staff.user.username})
                return JsonResponse(return_data, status=200)
            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)
   

def get_report_of_same_day(request):
    '''
    分单人员获取预约于当天的订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    if sessionid:
        try:
            session = Session.objects.get(session_key=sessionid)
            session_data = session.get_decoded()
            if session.expire_date > timezone.now():
                # api验证通过后，获取请求消息体中的内容
                user = get_user_from_sessionid(sessionid=sessionid)

                if user.last_name != 'admin':
                    return JsonResponse({'message': 'Permission error'})

                today_str = datetime.date.today().strftime("%Y/%m/%d")
                reports = call_report_table.objects.filter(
                    date__startswith=today_str
                )
                return_data = {
                    'message': 'Success',
                    'reports': []
                    }

                for report in reports:
                    return_data['reports'].append({
                        'reportId': report.id,
                        'userPhoneNumber': report.userPhoneNumber,
                        'address': report.address,
                        'issue': report.issue,
                        'status': report.status,
                        'date': report.date,
                        'call_date': report.call_date,
                        'workerName': report.workerName
                    })

                return JsonResponse(return_data, status=200)

            else:
                return JsonResponse({'message': 'Session has expired'}, status=200)
        except Session.DoesNotExist:
            return JsonResponse({'message': 'Invalid session'}, status=200)
    else:
        return JsonResponse({'message': 'No sessionid cookie'}, status=200)