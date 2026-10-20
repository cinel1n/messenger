import json
from .utils import check_message_rate_limit
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from login.models import User
from django.utils.decorators import method_decorator
from .models import Event, Message, Group
from django_ratelimit.decorators import ratelimit


class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        # персональная группа для точечных команд конкретному пользователю
        self.user_channel_group = f"user_{self.user.pk}"
        await self.channel_layer.group_add(self.user_channel_group, self.channel_name)

        await self.accept() # установление соединения
    

    async def valid_text_data(self,type=None, message_content=None):
        
        if type != "text_message":
            await self.send(text_data=json.dumps({
                "type": "error",
                "message":"Empty message or incorect type"
            }))
            return False
        
        if message_content is None or len(message_content) > 4096 or  message_content.strip() == "":
            await self.send(text_data=json.dumps({
                "type": "error",
                "message":"message too long or empry"
            }))
            return False

        return True

    async def receive(self, text_data=None, bytes_data=None):
        """
        После отправки сообщения пользователем на сервер
        Отправляет высокоуровневое событие в группу (channel_layer. self.send_json - низкоуровневое)
        """
        
        try:
            text_data = json.loads(text_data)

        except json.JSONDecodeError as decode:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message":f"json decode error: {decode.msg}"
            }))
            return 


        type = text_data.get("type", None)
        message_content = text_data.get("message", None)
        self.group_uuid = text_data.get("group_uuid")
        author = self.user
        group =await  database_sync_to_async(Group.objects.get)(
            uuid=self.group_uuid
        )

        if not await self.valid_text_data(type, message_content):
            return

        if not await check_message_rate_limit(self.user.id):  # check message
            await self.send(text_data=json.dumps({
                "type": "error",
                "message":"Too many messages. Try again later"
            }))
            return 

        await database_sync_to_async(Message.objects.create)(
            author=author,
            content=message_content,
            group=group
        )

        payload = {
            "type":"text_message", 
            "group_uuid": self.group_uuid, 
            "message": message_content,
            "author": author.username, 
            "avatar": author.get_avatar_url()
        }
        member_ids = [
            id_member async for id_member in group.members.values_list("id", flat=True)
        ]
        for id_member in member_ids:
            await self.channel_layer.group_send( # попадает в Redis
                f"user_{id_member}",
                {
                    "type": "text_message",
                    "payload": payload
                }
            )


    async def text_message(self, event):
        """
        после receive. отправка в браузер
        """
        payload = event.get("payload")
        await self.send(json.dumps(payload))

    async def event_message(self, event):
        payload = event.get("payload")
        await self.send(json.dumps(payload))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_channel_group,
            self.channel_name
        )
        if hasattr(self, "user_channel_group"): # проверка на атрибут
            await self.channel_layer.group_discard(self.user_channel_group, self.channel_name)

    async def force_disconnect(self, event):
        await self.close()