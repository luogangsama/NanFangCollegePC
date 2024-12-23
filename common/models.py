from django.db import models
from django.contrib.auth.models import AbstractUser, User
# Create your models here.

class Users(models.Model):
    # 用户名称
    username = models.CharField(max_length=200)
    # 用户密码
    password = models.CharField(max_length=256)
    # 用户身份 0: 普通用户; 1: 维修人员; 2: 订单分配人员
    label = models.CharField(max_length=2)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phoneNumber = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class call_report_table(models.Model):
    # 用户名称
    # username = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='call_report_table_profile_User')
    # 手机号码
    userPhoneNumber = models.CharField(max_length=11)
    # 地址
    address = models.CharField(max_length=50)
    # 问题
    issue = models.CharField(max_length=200)
    # 期待上门时间
    date = models.CharField(max_length=20)

    # 订单分配状态：0: 未分配; 1: 已分配
    allocationState = models.BooleanField(default=False)
    # 订单完成状态：0: 未完成; 1: 已完成
    completeState = models.BooleanField(default=False)

    # 维修人员手机号码
    workerPhoneNumber = models.CharField(max_length=11)
    # 维修人员姓名
    workerName = models.OneToOneField(User, on_delete=models.CASCADE, related_name='call_report_table_profile_worker')
