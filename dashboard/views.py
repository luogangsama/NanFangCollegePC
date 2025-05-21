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
from django.core.cache import cache

from loguru import logger
import hashlib
import json
import datetime


from SMS.views import send_verification_email
from SMS.views import verify_code

from unit.views import session_check, get_user_from_sessionid

# Create your views here.

@session_check
def get_user_info(request):
    '''
    获取用户信息，验证cookies可用后返回用户名
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    return JsonResponse({
        'message': 'Success',
        'username': user.username,
        'label': user.last_name
    })


@session_check
def call_report(request):
    '''
    接受前端发送的报单请求，并验证cookies后将订单存入数据库
    '''
    sessionid = request.COOKIES.get('sessionid')
    # session验证通过后，获取请求消息体中的内容
    user = get_user_from_sessionid(sessionid=sessionid)

    data = json.loads(request.body)
    userPhoneNumber = data['userPhoneNumber']
    address = data['address']
    issue = data['issue']
    date = data['date'] # 时间格式%Y-%m-%d %H:%M
    weekday = str(datetime.datetime.strptime(date, '%Y-%m-%d %H:%M').weekday() + 1)
    call_date = data['call_date'] # 订单提交的时间

    call_report_table.objects.create(
        user=user,
        userPhoneNumber=userPhoneNumber,
        address=address,
        issue=issue,
        date=date,
        call_date=call_date,
        weekday=weekday,
    )
    return JsonResponse({'message': 'Success', 'orderDetails': '订单提交成功'}, status=200)

@session_check
def user_get_history_report(request):
    '''
    响应前端用户所报修的历史订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    # 根据sessionid获取用户
    user = get_user_from_sessionid(sessionid=sessionid)
    
    report_infos = call_report_table.objects.all().order_by('-pk').filter(
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
        weekday = report_info.weekday

        return_report_info['report_info'].append({
            'reportId': report_id,
            'userPhoneNumber': userPhoneNumber,
            'address': address,
            'issue': issue,
            'status': status,
            'date': date,
            'call_date': call_date,
            'weekday': weekday
        })
        logger.success(f'{user.username}的历史订单: {return_report_info["report_info"]}')

    return JsonResponse(return_report_info, status=200)

@session_check
def worker_get_report_list(request):
    '''
    获取维修员的历史订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    my_reports = call_report_table.objects.all().order_by('-pk').filter(workerName=get_user_from_sessionid(sessionid=sessionid))
    if len(my_reports) == 0:
        return JsonResponse({'message': 'No my report'}, status=200)
    reports = []
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

@session_check
def log_out(request):
    '''
    验证前端请求的cookies后，搜索session数据库中符合sessionid的数据行予以删除或使其失效
    '''
    sessionid = request.COOKIES.get('sessionid')
    logout(request)
    return JsonResponse({'message': 'Success'}, status=200)

@session_check
def save_user_info(request):
    '''
    保存接收到的手机号码
    '''
    sessionid = request.COOKIES.get('sessionid')
    # 解析请求消息体
    data = json.loads(request.body)
# ===============================================================================
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
# ===============================================================================
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
    
@session_check
def get_phone_number(request):
    sessionid = request.COOKIES.get('sessionid')
    try:
        user = get_user_from_sessionid(sessionid=sessionid)
        phoneNumber = UserProfile.objects.get(user=user).phoneNumber
        if phoneNumber == 'None':
            return JsonResponse({'message': 'No phone number'}, status=200)
        return JsonResponse({'message': 'Success', 'phoneNumber': phoneNumber}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'message': 'No phone number'}, status=200)

@session_check
def renew_password(request):
    '''
    修改密码
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    # 获取请求消息体中的内容
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

@session_check
def assign_order(request):
    '''
    管理员分配订单
    '''
    sessionid = request.COOKIES.get('sessionid')
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
            return JsonResponse({'message': 'Permission error'}, status=403)
    except User.DoesNotExist:
        return JsonResponse({'message': 'This worker is no exist'}, status=200)

    try:
        report_id = int(data['reportId'])
        report = call_report_table.objects.get(id=report_id)
        if report.status != '0':
            # 订单已被分配
            return JsonResponse({'message': 'This report is allocated'}, status=200)
        # 向订单表中填入相关信息并改变状态
        report.workerName = worker
        report.workerPhoneNumber = UserProfile.objects.get(user=worker).phoneNumber
        report.status = '1'
        report.save()

        return JsonResponse({'message': 'Success'}, status=200)
    except call_report_table.DoesNotExist:
        return JsonResponse({'message': 'This report is no exist'}, status=200)

@session_check
def complete_report(request):
    '''
    用户结单
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    # 获取请求消息体中的内容
    data = json.loads(request.body)
    reportId = int(data['reportId'])
    try:
        report = call_report_table.objects.get(pk=reportId)
    except:
        return JsonResponse({'message': 'This report is no exist'}, status=200)
    if report.status == '2':
        return JsonResponse({'message': 'This report is completed'}, status=200)
        
    report.status = '2'
    report.save()
    return JsonResponse({'message': 'Success'}, status=200)

@session_check
def cancel_report(request):
    '''
    用户撤销报单
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    # 获取请求消息体中的内容
    data = json.loads(request.body)
    reportId = int(data['reportId'])

    try:
        report = call_report_table.objects.get(id=reportId)
        report.status = '3'
        report.save()
        return JsonResponse({'message': 'Success'}, status=200)
    except:
        return JsonResponse({'message': 'This report is no exist'}, status=200)

@session_check
def reset_email_send_code(request):
    '''
    更改邮箱时发送验证码
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    old_email = user.email
    # 向用户注册账户时绑定的邮箱发送验证码
    return send_verification_email(old_email)

@session_check
def reset_email(request):
    '''
    验证邮箱验证码后修改用户的邮箱
    '''
    sessionid = request.COOKIES.get('sessionid')
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

@session_check
def get_staff_of_same_day(request):
    '''
    获取与分单人员同一天值班的人员名单
    '''
    sessionid = request.COOKIES.get('sessionid')
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
    logger.success(f'与{user.username}同一天工作的人员名单:\n{return_data["workers"]}')
    return JsonResponse(return_data, status=200)
   
@session_check
def get_report_of_same_day(request):
    '''
    分单人员获取预约于当天的订单
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    if user.last_name != 'admin':
        return JsonResponse({'message': 'Permission error'})
    reports = call_report_table.objects.all().order_by('-pk').filter(
        weekday=UserProfile.objects.get(user=user).dutyTime
        )
    return_data = {
        'message': 'Success',
        'reports': []
        }
    for report in reports:
        if report.workerName:
            workerName = report.workerName.username
        else:
            workerName = 'None'
        return_data['reports'].append({
            'reportId': report.id,
            'userPhoneNumber': report.userPhoneNumber,
            'address': report.address,
            'issue': report.issue,
            'status': report.status,
            'date': report.date,
            'call_date': report.call_date,
            'workerName': workerName,
        })
    logger.success(f'{user.username}管理的订单:\n{return_data["reports"]}')
    return JsonResponse(return_data, status=200)

@session_check
def submit_rating(request):
    data = json.loads(request.body)
    reportId = data['reportId']
    rating = data['rating']
    if rating > 5 or rating < 0:
        return JsonResponse({'message': 'Invalid parameters'}, status=400)

    comment = data['comment']
    try:
        report = call_report_table.objects.get(pk=reportId)
        print(report.rating)
        if report.rating != '0':
            return JsonResponse({'message': 'Invalid report status'})
        report.rating = rating
        report.comment = comment
        report.save()
        return JsonResponse({'message': 'Success'}, status=200)
    except:
        return JsonResponse({'message': 'Report not found'}, status=400)
