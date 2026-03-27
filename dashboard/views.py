from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.timezone import now
from django.db import transaction
from common.models import call_report_table, OrderAssignment
from common.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.contrib.auth.hashers import check_password
from django.core.cache import cache

from loguru import logger
import hashlib
import json
import datetime
from lxml import etree
import time


from SMS.views import send_verification_email
from SMS.views import verify_code

from unit.views import session_check, get_user_from_sessionid, validMessageFromWeiXin, order_broadcast_to_dingtalk

# Create your views here.

@logger.catch
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
        'label': user.profile.identity
    })


@logger.catch
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

    '''
    钉钉播报
    '''
    # 获取当前所有未分配订单
    unassigned_reports = call_report_table.objects.filter(status='0').order_by('pk')
    msg = "未分配订单列表：\n"
    for report in unassigned_reports:
        msg += f"订单ID: {report.id}\n"
        msg += f"用户名: {report.user.username}\n"
        msg += f"电话: {report.userPhoneNumber}\n"
        msg += f"地址: {report.address}\n"
        msg += f"问题: {report.issue}\n"
        msg += f"预约时间: {report.date}\n"
        msg += "========================\n"
    order_broadcast_to_dingtalk(msg)
    return JsonResponse({'message': 'Success', 'orderDetails': '订单提交成功'}, status=200)

@logger.catch
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
        # logger.success(f'{user.username}的历史订单: {return_report_info["report_info"]}')

    return JsonResponse(return_report_info, status=200)

@logger.catch
@session_check
def worker_get_report_list(request):
    """
    获取维修员的历史订单
    支持多人员分配：通过 OrderAssignment 表查询
    """
    sessionid = request.COOKIES.get('sessionid')
    worker = get_user_from_sessionid(sessionid=sessionid)
    
    assignment_report_ids = OrderAssignment.objects.filter(
        worker=worker,
        status='active'
    ).values_list('report_id', flat=True)
    
    my_reports = call_report_table.objects.all().order_by('-pk').filter(
        id__in=assignment_report_ids
    )
    
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

@logger.catch
@session_check
def log_out(request):
    '''
    验证前端请求的cookies后，搜索session数据库中符合sessionid的数据行予以删除或使其失效
    '''
    sessionid = request.COOKIES.get('sessionid')
    logout(request)
    return JsonResponse({'message': 'Success'}, status=200)

@logger.catch
@session_check
def save_user_info(request):
    '''
    保存接收到的手机号码
    '''
    sessionid = request.COOKIES.get('sessionid')
    # 解析请求消息体
    data = json.loads(request.body)
# ===============================================================================
    # try:
    #     new_name = data['newName']
    # except:
    #     new_name = get_user_from_sessionid(sessionid=sessionid).username
    # try:
    #     new_phone_number = data['phoneNumber']
    # except:
    #     try:
    #         new_phone_number = UserProfile.objects.get(
    #             user=get_user_from_sessionid(sessionid=sessionid)
    #         ).phoneNumber
    #     except:
    #         new_phone_number = None
    # #以上一块代码的目的是为了判断用户是只想改任意一项还是两项都要改。
    # #电话号码的部分的基本逻辑：若消息体中没有phoneNumber则先查找一下UserProfile表中是否有这个用户对应的号码，
    # #若是有则直接拿出来赋值给new_phone_number，这样更新后号码不变，若是查找不到，就预设一个None

    '''
    以上为旧版本逻辑，在字典中直接使用索引是不安全的写法，所以使用了大量的的错误处理来满足逻辑，
    现已改为使用get方法这种更安全的方式获取数据，以及使用if的语法糖压缩代码量，整体逻辑不变
    '''
    new_name = data.get('newName')
    new_name = new_name if new_name else get_user_from_sessionid(sessionid=sessionid).username

    new_phone_number = data.get('phoneNumber')
    new_phone_number = new_phone_number if new_phone_number else UserProfile.objects.get(
        user=get_user_from_sessionid(sessionid=sessionid)
    ).phoneNumber
    
# ===============================================================================
    # # 判断可能出现的新旧名相同的情况
    # if new_name == get_user_from_sessionid(sessionid=sessionid).username:
    #     # 首先更改auth_user表中的username
    #     user = User.objects.get(username=get_user_from_sessionid(sessionid=sessionid).username)
    #     user.username = new_name
    #     user.save()

    #     # 然后根据新user去更改phone number
    #     userProfile = UserProfile.objects.get(user=user)
    #     userProfile.phoneNumber = new_phone_number
    #     userProfile.save()
    # else:
    #     if len(User.objects.filter(username=new_name)) > 0:
    #         return JsonResponse({'message': 'This user is existed'})
    #     user = User.objects.get(username=get_user_from_sessionid(sessionid=sessionid).username)
    #     user.username = new_name
    #     user.save()

    #     # 然后根据新user去更改phone number
    #     userProfile = UserProfile.objects.get(user=user)
    #     userProfile.phoneNumber = new_phone_number
    #     userProfile.save()
    
    # 根据发起请求的用户的session获取其id
    user = get_user_from_sessionid(sessionid=sessionid)
    user_id_with_session_id = user.pk

    # 根据新名称查找用户id,若查到则返回其id，否则设为为发起请求的用户的id
    user_id_with_new_name = User.objects.filter(username=new_name).first().pk \
        if User.objects.filter(username=new_name).first() \
        else user_id_with_session_id

    if user_id_with_new_name != user_id_with_session_id:
        # 判断这两个id是否相等，就可以判断新名称是否指向另一个用户
        # 是的话就返回用户名称已被占用的响应
        return JsonResponse({'message': 'This user is existed'})
    
    # 更新表中的用户数据
    user.username = new_name
    user.save()
    userProfile = UserProfile.objects.get(user=user)
    userProfile.phoneNumber = new_phone_number
    userProfile.save()


        
    # 登出再登入（刷新sessionid）
    logout(request=request)
    login(request=request, user=user)
    
    return JsonResponse({'message': 'Success'}, status=200)
    
@logger.catch
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

@logger.catch
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

@logger.catch
@session_check
def assign_order(request):
    """
    管理员分配订单 - 支持多人员分配
    支持两种请求格式:
    1. 新格式: {"reportId": "xxx", "workerNames": ["张三", "李四"]}
    2. 向后兼容: {"reportId": "xxx", "workerName": "张三"}
    """
    MAX_WORKERS_PER_ORDER = 5
    
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    if user.profile.identity != 'admin':
        return JsonResponse({'message': 'Permission error'}, status=403)
    
    data = json.loads(request.body)
    report_id = data.get('reportId')
    worker_names = data.get('workerNames', [])
    
    if not worker_names:
        single_worker = data.get('workerName')
        if single_worker:
            worker_names = [single_worker]
    
    if not report_id or not worker_names:
        return JsonResponse({'message': 'Invalid parameters'}, status=400)
    
    if len(worker_names) > MAX_WORKERS_PER_ORDER:
        return JsonResponse({
            'message': 'Max workers exceeded',
            'error': {
                'code': 'MAX_WORKERS_EXCEEDED',
                'details': f'单个订单最多分配 {MAX_WORKERS_PER_ORDER} 名维修人员'
            }
        }, status=400)
    
    try:
        report_id_int = int(report_id)
        report = call_report_table.objects.get(id=report_id_int)
    except (ValueError, call_report_table.DoesNotExist):
        return JsonResponse({'message': 'This report is no exist'}, status=404)
    
    if report.status != '0':
        return JsonResponse({'message': 'This report is allocated'}, status=400)
    
    workers = []
    for worker_name in worker_names:
        try:
            worker = User.objects.get(username=worker_name)
            if worker.profile.identity not in ['worker', 'admin']:
                return JsonResponse({
                    'message': 'Invalid worker',
                    'error': {
                        'code': 'INVALID_WORKER',
                        'details': f'维修人员 {worker_name} 权限不足'
                    }
                }, status=400)
            workers.append(worker)
        except User.DoesNotExist:
            return JsonResponse({
                'message': 'Invalid worker',
                'error': {
                    'code': 'INVALID_WORKER',
                    'details': f'维修人员 {worker_name} 不存在'
                }
            }, status=400)
    
    existing_assignments = OrderAssignment.objects.filter(
        report_id=report_id_int,
        worker__in=workers,
        status='active'
    )
    if existing_assignments.exists():
        existing_names = [a.worker.username for a in existing_assignments]
        return JsonResponse({
            'message': 'Duplicate assignment',
            'error': {
                'code': 'DUPLICATE_ASSIGNMENT',
                'details': f'部分维修人员已被分配到此订单: {", ".join(existing_names)}'
            }
        }, status=400)
    
    try:
        with transaction.atomic():
            for worker in workers:
                OrderAssignment.objects.create(
                    report=report,
                    worker=worker,
                    assigned_by=user
                )
            
            report.status = '1'
            report.save()
        
        assigned_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return JsonResponse({
            'message': 'Success',
            'data': {
                'reportId': report_id,
                'assignedWorkers': worker_names,
                'assignedAt': assigned_at
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f'分配订单失败: {str(e)}')
        return JsonResponse({'message': 'Internal server error'}, status=500)

@logger.catch
@session_check
def complete_report(request):
    """
    用户结单
    同时更新 OrderAssignment 状态为 completed
    """
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    data = json.loads(request.body)
    reportId = int(data['reportId'])
    try:
        report = call_report_table.objects.get(pk=reportId)
    except:
        return JsonResponse({'message': 'This report is no exist'}, status=200)
    if report.status == '2':
        return JsonResponse({'message': 'This report is completed'}, status=200)
    
    with transaction.atomic():
        report.status = '2'
        report.save()
        
        OrderAssignment.objects.filter(
            report=report,
            status='active'
        ).update(status='completed')
    
    return JsonResponse({'message': 'Success'}, status=200)

@logger.catch
@session_check
def cancel_report(request):
    """
    用户撤销报单
    同时更新 OrderAssignment 状态为 cancelled
    """
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    data = json.loads(request.body)
    reportId = int(data['reportId'])

    try:
        report = call_report_table.objects.get(id=reportId)
        
        with transaction.atomic():
            report.status = '3'
            report.save()
            
            OrderAssignment.objects.filter(
                report=report,
                status='active'
            ).update(status='cancelled')
        
        return JsonResponse({'message': 'Success'}, status=200)
    except:
        return JsonResponse({'message': 'This report is no exist'}, status=200)

@logger.catch
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

@logger.catch
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

@logger.catch
@session_check
def get_staff_of_same_day(request):
    """
    获取与分单人员同一天值班的人员名单
    返回包含当前订单数的维修人员列表
    """
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
        current_assignments = OrderAssignment.objects.filter(
            worker=staff.user,
            status='active'
        ).count()
        
        return_data['workers'].append({
            'username': staff.user.username,
            'available': True,
            'currentAssignments': current_assignments
        })
    
    return JsonResponse(return_data, status=200)
   
@logger.catch
@session_check
def get_report_of_same_day(request):
    """
    分单人员获取预约于当天的订单
    返回包含多人员分配信息的订单列表
    """
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    if user.profile.identity != 'admin':
        return JsonResponse({'message': 'Permission error'}, status=403)
    
    reports = call_report_table.objects.all().order_by('-pk').filter(
        weekday=UserProfile.objects.get(user=user).dutyTime
    )
    
    return_data = {
        'message': 'Success',
        'reports': []
    }
    
    for report in reports:
        assignments = OrderAssignment.objects.filter(
            report=report,
            status='active'
        ).order_by('assigned_at')
        
        worker_names = [a.worker.username for a in assignments]
        
        if not worker_names and report.workerName:
            worker_names = [report.workerName.username]
        
        worker_name_str = ', '.join(worker_names) if worker_names else 'None'
        
        return_data['reports'].append({
            'reportId': report.id,
            'userPhoneNumber': report.userPhoneNumber,
            'address': report.address,
            'issue': report.issue,
            'status': report.status,
            'date': report.date,
            'call_date': report.call_date,
            'workerNames': worker_names,
            'workerName': worker_name_str,
        })
    
    return JsonResponse(return_data, status=200)

@logger.catch
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
        print(report)
        print(type(report))
        if report.rating != '0':
            return JsonResponse({'message': 'Invalid report status'})
        report.rating = rating
        report.comment = comment
        report.save()
        return JsonResponse({'message': 'Success'}, status=200)
    except:
        return JsonResponse({'message': 'Report not found'}, status=400)


@logger.catch
def parse_wechat_message(request):
    """解析微信XML消息"""
    xml_data = request.body
    xml_tree = etree.fromstring(xml_data)
    return {
        "to_user": xml_tree.find("ToUserName").text,
        "from_user": xml_tree.find("FromUserName").text,
        "msg_type": xml_tree.find("MsgType").text,
        "content": xml_tree.find("Content").text if xml_tree.find("Content") is not None else "",
        "msg_id": xml_tree.find("MsgId").text
    }

@logger.catch
def build_text_response(to_user, from_user, content):
    """构造文本响应XML"""
    return f"""
    <xml>
        <ToUserName><![CDATA[{to_user}]]></ToUserName>
        <FromUserName><![CDATA[{from_user}]]></FromUserName>
        <CreateTime>{int(time.time())}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
    </xml>
    """

@logger.catch
@session_check
def change_duty_time(request):
    '''
    修改值班时间
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    if user.profile.identity == 'customer':
        return JsonResponse({'message': 'Permission error'}, status=403)
    data = json.loads(request.body)
    new_duty_time = data['duty_time']
    user_profile = UserProfile.objects.get(user=user)
    user_profile.dutyTime = new_duty_time
    user_profile.save()
    return JsonResponse({'message': 'Success'}, status=200)

@logger.catch
@session_check
def get_duty_time(request):
    '''
    获取工作人员值班时间
    '''
    sessionid = request.COOKIES.get('sessionid')
    user = get_user_from_sessionid(sessionid=sessionid)
    if user.profile.identity == 'customer':
        return JsonResponse({'message': 'Permission error'}, status=403)
    user_profile = UserProfile.objects.get(user=user)
    duty_time = user_profile.dutyTime
    return JsonResponse({
        'message': 'Success',
        'dutyTime': duty_time
    }, status=200)

@logger.catch
@validMessageFromWeiXin
def weixinTest(request):
    if request.method == "POST":
        try:
            msg = parse_wechat_message(request)
            logger.info(f"收到消息: {msg['content']}")

            # 基础回复（echo模式）
            reply_content = f"已收到：{msg['content']}"
            
            return HttpResponse(
                build_text_response(msg['to_user'], msg['from_user'], reply_content),
                content_type="application/xml"
            )
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return HttpResponse("ERROR", status=500)
    else:
        return HttpResponse("请使用POST请求", status=405)