from django.urls import re_path
from . import consumers # 类似于views.py功能的文件，需要新建

websocket_urlpatterns = [
    re_path(r'/ws/message/(?P<user_id>\w+)/(?P<report_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
