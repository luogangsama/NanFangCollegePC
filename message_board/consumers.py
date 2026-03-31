import json
import html
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs
from common.models import call_report_table, report_message_board_record
from django.utils import timezone
from django.core.cache import cache

MESSAGE_RATE_LIMIT = 2
RATE_LIMIT_WINDOW = 1

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        self.report_id = query_params.get("report_id", [None])[0]
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.username = user.username
        self.room_group_name = f'message_{self.report_id}'

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 接收 WebSocket 消息
    async def receive(self, text_data):
        MAX_MESSAGE_LENGTH = 1000
        
        user_key = f"ws_rate_limit_{self.user.id}_{self.report_id}"
        last_time = await sync_to_async(cache.get)(user_key)
        current_time = time.time()
        
        if last_time and current_time - last_time < RATE_LIMIT_WINDOW:
            await self.send(json.dumps({'error': 'Rate limit exceeded, please wait'}))
            return
        
        await sync_to_async(cache.set)(user_key, current_time, timeout=60)
        
        if len(text_data) > MAX_MESSAGE_LENGTH:
            await self.send(json.dumps({'error': 'Message too long'}))
            return
        
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'error': 'Invalid JSON format'}))
            return
        
        if not isinstance(data, dict):
            await self.send(json.dumps({'error': 'Invalid message type, expected object'}))
            return
        
        if 'message' not in data:
            await self.send(json.dumps({'error': 'Missing required field: message'}))
            return
        
        message = data['message']
        
        if not isinstance(message, str):
            await self.send(json.dumps({'error': 'Message must be a string'}))
            return
        
        message = html.escape(message.strip())
        
        if not message:
            await self.send(json.dumps({'error': 'Message cannot be empty'}))
            return
        
        # 发送到房间组
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'username': self.username,
                    'message': message
                }
            }
        )
        print(f'talker: {self.username}, message: {message}')
        utc_now = timezone.now()
        now = timezone.localtime(utc_now)
        reportId = int(self.report_id)
        # 根据订单号获取订单对象
        report = await sync_to_async(call_report_table.objects.get)(id=reportId)
        # 根据订单对象往留言记录表中插入记录
        await sync_to_async(report_message_board_record.objects.create)(
            report=report,
            user=self.user,
            message=message,
            date=now
        )

    # 从房间组接收消息
    async def chat_message(self, event):
        message = event['message']
        # 发送到 WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

# 测试代码
# class MessageConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         user = '测试'
#         query_string = self.scope["query_string"].decode()
#         query_params = parse_qs(query_string)

#         self.report_id = query_params.get("report_id", [None])[0]

#         self.user = user
#         self.username = user
#         self.room_group_name = f'message_{self.report_id}'

#         # 加入房间组
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         # 离开房间组
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     # 接收 WebSocket 消息
#     async def receive(self, text_data):
#         message = eval(text_data)['message']
#         # 发送到房间组
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': {
#                     'username': self.username,
#                     'message': message
#                 }
#             }
#         )
#         print(f'talker: {self.username}, message: {message}')

#     # 从房间组接收消息
#     async def chat_message(self, event):
#         message = event['message']
#         # 发送到 WebSocket
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))