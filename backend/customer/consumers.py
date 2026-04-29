import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Thêm client vào nhóm 'status_updates'
        await self.channel_layer.group_add(
            'status_updates',
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Xóa client khỏi nhóm 'status_updates'
        await self.channel_layer.group_discard(
            'status_updates',
            self.channel_name
        )

    # Hàm này xử lý thông báo 'update_status' từ server
    async def update_status(self, event):
        message = event['message']

        # Gửi thông báo cho client
        await self.send(text_data=json.dumps({
            'message': message
        }))
