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
        self.group_uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
        self.group = await database_sync_to_async(Group.objects.get)(uuid=self.group_uuid)
        await self.channel_layer.group_add( # добавление в слой
            self.group_uuid, self.channel_name) # channel_name - адрес websocket соединения

        self.user = self.scope["user"]

        is_member = await database_sync_to_async(
            lambda: Group.objects.filter(
                uuid=self.group_uuid,
                members=self.user,
            ).first()
        )()

        if not is_member:
            await self.close()
            return

        # персональная группа для точечных команд конкретному пользователю
        self.user_channel_group = f"user_{self.user.pk}"
        await self.channel_layer.group_add(self.user_channel_group, self.channel_name)


        await self.accept() # установление соединения
        

    async def receive(self, text_data=None, bytes_data=None):
        """
        После отправки сообщения пользователем на сервер
        Отправляет высокоуровневое событие в группу (channel_layer. self.send_json - низкоуровневое)
        """

        text_data = json.loads(text_data)
        type = text_data.get("type", None)
        message_content = text_data.get("message", None)
        author = self.user

        if not await check_message_rate_limit(self.user.id):  # check message
            await self.send(text_data=json.dumps({
                "type": "error",
                "message":"Too many messages. Try again later"
            }))
            return 

        if type == "text_message":
            await database_sync_to_async(Message.objects.create)(
                author=author,
                content=message_content,
                group=self.group
            )

        await self.channel_layer.group_send( # попадает в Redis
            self.group_uuid,
            {
                "type": "text_message",
                "message": message_content,
                "author": author.username
            }
        )

    async def text_message(self, event):
        """
        после receive 
        """
        message = event.get("message")

        returned_data = {
            "type": "text_message",
            "message": message,
        }
        await self.send(json.dumps(returned_data))

    async def event_message(self, event):
        message = event.get("message")
        user = event.get("user", None)
        status = event.get("status", None)

        returned_data = {
            "type": "event_message",
            "message": message,
            "status": status,
            "user": user
        }
        await self.send(json.dumps(returned_data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_uuid,
            self.channel_name
        )
        if hasattr(self, "user_channel_group"): # проверка на атрибут
            await self.channel_layer.group_discard(self.user_channel_group, self.channel_name)

    async def force_disconnect(self, event):
        await self.close()