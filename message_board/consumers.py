import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.report_id = self.scope['url_route']['kwargs']['report_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
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
        data = json.loads(text_data)
        message = data['message']

        # 发送到房间组
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # 从房间组接收消息
    async def chat_message(self, event):
        message = event['message']

        # 发送到 WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
