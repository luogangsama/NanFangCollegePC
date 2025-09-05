from django.db import models
from django.contrib.auth.models import AbstractUser, User
# Create your models here.

# class Users(models.Model):
#     # 用户名称
#     username = models.CharField(max_length=200)
#     # 用户密码
#     password = models.CharField(max_length=256)
#     # 用户身份 0: 普通用户; 1: 维修人员; 2: 订单分配人员
#     label = models.CharField(max_length=2)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    location = models.JSONField(default=dict, blank=True, null=True)
    locationExpiresAt = models.DateTimeField(blank=True, null=True)
    phoneNumber = models.CharField(max_length=11)
    identity = models.CharField(max_length=8, default='customer')
    dutyTime = models.CharField(max_length=1, default='0')

    def __str__(self):
        return f"{self.user.username}'s Profile"

class locationWeather(models.Model):
    location = models.JSONField(default=dict)
    weather = models.JSONField(help_text='')
    expiresAt = models.DateTimeField()

class call_report_table(models.Model):
    # 用户名称
    # username = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_report_table_profile_User')
    # 手机号码
    userPhoneNumber = models.CharField(max_length=11)
    # 地址
    address = models.CharField(max_length=50)
    # 问题
    issue = models.CharField(max_length=200)
    # 预约维修时间
    date = models.CharField(max_length=50)
    # 预约时间所对应的星期
    weekday = models.CharField(max_length=1)
    # 订单提交时间
    call_date = models.CharField(max_length=50)
    # 订单状态
    status = models.CharField(max_length=1, default='0')

    # 维修人员手机号码
    workerPhoneNumber = models.CharField(max_length=11)
    # 维修人员姓名
    workerName = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_report_table_profile_worker', null=True, blank=True)

    # 评分
    rating = models.CharField(max_length=1, default='0')
    # 评价
    comment = models.CharField(max_length=200, default='')

class report_message_board_record(models.Model):
    # 订单
    report = models.ForeignKey(call_report_table, on_delete=models.CASCADE, related_name="message_reportId")
    # 留言人
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_record_User")
    # 留言内容
    message = models.CharField(max_length=500)
    # 留言时间
    date = models.CharField(max_length=50)
