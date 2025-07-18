"""
Django settings for NanFangCollegePC project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tqo4(yo8ht-7$5e8p6-*d+!ti+nsj&dz-2&+*-(^jovw)wlu0@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', 'gznfpc.cn', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'django.contrib.staticfiles',
    
    'common.apps.CommonConfig',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'NanFangCollegePC.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'NanFangCollegePC.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


ASGI_APPLICATION = 'NanFangCollegePC.asgi.application'
# 配置通道层，用于多实例通信
# 仅单机调试可省略，建议使用 Redis
CHANNEL_LAYERS = {
    "default": {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'COFIG': {
            'hosts': [('127.0.0.1', 6379)],
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # sessions

# # 默认存储在数据库中
# SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# # 会话 Cookie 的配置
# SESSION_COOKIE_NAME = 'sessionid'  # 默认会话 Cookie 的名称
# SESSION_COOKIE_AGE = 1209600      # 2 周，单位秒
# SESSION_COOKIE_SECURE = False     # 如果启用 HTTPS，则设为 True
# SESSION_COOKIE_HTTPONLY = True    # 禁止 JavaScript 访问 Cookie
# SESSION_SAVE_EVERY_REQUEST = True # 每次请求都刷新会话的过期时间

# 发送邮箱验证码
EMAIL_USE_SSL = True
EMAIL_HOST = "smtp.qq.com" # 服务器
EMAIL_PORT = 465
EMAIL_HOST_USER = '3070845578@qq.com'
EMAIL_FROM = '3070845578@qq.com'
try:
    with open("/root/code.txt", 'r') as f:
        EMAIL_HOST_PASSWORD = f.readline()
        EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD[0: -1]
except :
    print("请将 code.txt放置于根目录下且确保其内容是正确的授权码，然后重启项目")
    EMAIL_HOST_PASSWORD = ''

from NanFangCollegePC.loguru_config import logger  # 引入 loguru 的配置文件

# 配置 Django 的日志系统，转发到 loguru
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # 不禁用其他日志
    "handlers": {
        "loguru": {
            "level": "INFO",
            "class": "NanFangCollegePC.loguru_config.InterceptHandler",  # 使用 loguru 的处理器
        },
    },
    "root": {
        "handlers": ["loguru"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["loguru"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["loguru"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')