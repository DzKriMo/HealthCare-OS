import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        has_access = await self._check_room_access(user, self.room_id)
        if not has_access:
            await self.close()
            return

        self.user = user
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type", "message")

        if msg_type == "message":
            content = data.get("content", "").strip()
            if not content:
                return
            message = await self._save_message(self.room_id, self.user, content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "id": str(message["id"]),
                    "sender_id": str(message["sender_id"]),
                    "sender_name": message["sender_name"],
                    "content": message["content"],
                    "created_at": message["created_at"],
                },
            )

        elif msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": str(self.user.id),
                    "user_name": self.user.full_name,
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "id": event["id"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "content": event["content"],
            "created_at": event["created_at"],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
        }))

    @database_sync_to_async
    def _check_room_access(self, user, room_id):
        from .models import ChatRoom
        return ChatRoom.objects.filter(id=room_id, participants=user).exists()

    @database_sync_to_async
    def _save_message(self, room_id, user, content):
        from .models import ChatRoom, ChatMessage
        import uuid
        room = ChatRoom.objects.get(id=room_id)
        msg = ChatMessage.objects.create(
            id=uuid.uuid4(),
            room=room,
            sender=user,
            content=content,
        )
        return {
            "id": msg.id,
            "sender_id": user.id,
            "sender_name": user.full_name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }


class VideoSignalConsumer(AsyncWebsocketConsumer):
    """WebRTC signaling for video calls."""

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"video_{self.room_name}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        signal_type = data.get("type")

        if signal_type in ("offer", "answer", "ice-candidate"):
            data["sender_id"] = str(self.user.id)
            data["sender_name"] = self.user.full_name
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video_signal",
                    "data": data,
                },
            )

    async def video_signal(self, event):
        await self.send(text_data=json.dumps(event["data"]))
