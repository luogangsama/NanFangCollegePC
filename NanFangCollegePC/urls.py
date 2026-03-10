"""
URL configuration for NanFangCollegePC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from register.views import register
from register.views import worker_register
from register.views import register_send_code
from login.views import Signin
from login.views import AutoSignin
from login.views import ForgetPassword
from login.views import ForgetPasswordSendCode
from login.views import forget_password_send_code

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/register_send_code/', register_send_code),
    path('api/users/register/', register),
    path('api/users/worker_register/', worker_register),
    path('api/users/login/', Signin.as_view(), name='signin'),
    path('api/users/validate-session/', AutoSignin.as_view(), name='auto_signin'),
    path('api/users/forget_password/', ForgetPassword.as_view(), name='forget_password'),
    path('api/users/forget_password_send_code/', ForgetPasswordSendCode.as_view(), name='forget_password_send_code'),

    path('api/dashboard/', include('dashboard.urls')),
    path('api/unit/', include('unit.urls')),
    path('api/message_board/', include('message_board.urls')),
]
