from django.urls import re_path
from message_board import consumers # 类似于views.py功能的文件，需要新建

websocket_urlpatterns = [
    re_path(r'ws/message/(?P<user_id>\d+)/(?P<report_id>\d+)/$', consumers.MessageConsumer.as_asgi()),
]
