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
from login.views import signin
from login.views import auto_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/register/', register),
    path('api/users/login/', signin),
    path('api/users/validate-session/', auto_login),

    path('api/dashboard/', include('dashboard.urls')),
]
