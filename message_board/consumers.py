import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs
from common.models import call_report_table, report_message_board_record

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
        message = eval(text_data)['message']
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

    # 从房间组接收消息
    async def chat_message(self, event):
        message = event['message']

        # 发送到 WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
        reportId = int(self.report_id)
        # 根据订单号获取订单对象
        report = await sync_to_async(call_report_table.objects.get)(id=reportId)
        # 根据订单对象往留言记录表中插入记录
        report_message_board_record.objects.create(
            report=report,
            user=self.user,
            message=message
        )