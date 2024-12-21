from django.db import models

# Create your models here.

class Users(models.Model):
    # 用户名称
    username = models.CharField(max_length=200)
    # 用户密码
    password = models.CharField(max_length=256)
    # 用户身份 0: 普通用户; 1: 维修人员; 2: 订单分配人员
    label = models.CharField(max_length=2)