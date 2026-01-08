import json

from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from login.models import User

from .models import Event, Message, Group


class JoinAndLeave(WebsocketConsumer):
    def connect(self):
        print("WORK!")
        self.user = self.scope["user"]
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        print("WORK!")
        type = text_data.get("type", None)
        if type:
            data = text_data.get("data", None)

        if type == "leave_group":
            self.leave_group(data)
        elif type == "join_group":
            self.join_group(data)

    def leave_group(self, group_uuid):
        group = Group.objects.get(uuid=group_uuid)
        group.remove_user_from_group(self.user)
        data = {
            "type": "leave_group",
            "data": group_uuid
        }
        self.send(json.dumps(data))

    def join_group(self, group_uuid):
        group = Group.objects.get(uuid=group_uuid)
        group.add_user_to_group(self.user)
        data = {
            "type": "join_group",
            "data": group_uuid
        }
        self.send(json.dumps(data))


class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
        self.group = await database_sync_to_async(Group.objects.get)(uuid=self.group_uuid)
        await self.channel_layer.group_add( # добавление в слой
            self.group_uuid, self.channel_name) # channel_name - адрес websocket соединения

        self.user = self.scope["user"]
        await self.accept() # установление соединения

    async def receive(self, text_data=None, bytes_data=None):
        """
        Отправляет высокоуровневое событие в группу (channel_layer. self.send_json - низкоуровневое)
        """

        text_data = json.loads(text_data)
        type = text_data.get("type", None)
        message_content = text_data.get("message", None)
        author = text_data.get("author", None)

        if type == "text_message":
            user = await database_sync_to_async(User.objects.get)(username=author)
            await database_sync_to_async(Message.objects.create)(
                author=user,
                content=message_content,
                group=self.group
            )

        await self.channel_layer.group_send(
            self.group_uuid,
            {
                "type": "text_message",
                "message": message_content,
                "author": author
            }
        )

    async def text_message(self, event):
        """
        Вызывается, когда кто-то отправил сообщение в чат.
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