import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Check if user is participant in this chat
        if not await self.is_chat_participant():
            await self.close()
            return

        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        # Update user online status
        await self.update_user_status(True)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

        # Update user offline status
        await self.update_user_status(False)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')

            if message_type == 'chat_message':
                message_content = text_data_json.get('message', '').strip()

                if not message_content:
                    return

                # Save message to database
                message_data = await self.save_message(message_content)

                if message_data:
                    # Send message to chat group with proper timestamp
                    await self.channel_layer.group_send(
                        self.chat_group_name,
                        {
                            'type': 'chat_message',
                            'message': message_content,
                            'sender': self.user.username,
                            'sender_id': self.user.id,
                            'timestamp': message_data['timestamp'],
                            'message_id': message_data['id'],
                        }
                    )

            elif message_type == 'typing':
                # Handle typing indicator
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'typing_indicator',
                        'user': self.user.username,
                        'user_id': self.user.id,
                        'is_typing': text_data_json.get('is_typing', False),
                    }
                )

        except Exception:
            pass

    async def chat_message(self, event):
        # Send message to WebSocket
        try:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': event['message'],
                'sender': event['sender'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp'],
                'message_id': event['message_id'],
            }))
        except Exception:
            pass

    async def typing_indicator(self, event):
        # Don't send typing indicator to the sender
        if event['user_id'] != self.user.id:
            try:
                await self.send(text_data=json.dumps({
                    'type': 'typing_indicator',
                    'user': event['user'],
                    'is_typing': event['is_typing'],
                }))
            except Exception:
                pass

    @database_sync_to_async
    def is_chat_participant(self):
        from .models import Chat
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return chat.participants.filter(id=self.user.id).exists()
        except Exception:
            return False

    @database_sync_to_async
    def save_message(self, content):
        from .models import Chat, Message
        try:
            chat = Chat.objects.get(id=self.chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content
            )
            # Update chat's updated_at field
            chat.updated_at = timezone.now()
            chat.save()

            # Return timestamp in the format we want (like 5:49 PM)
            return {
                'id': message.id,
                'timestamp': message.timestamp.strftime('%I:%M %p').lstrip('0'),
            }
        except Exception:
            return None

    @database_sync_to_async
    def update_user_status(self, is_online):
        from Account.models import UserProfile
        try:
            profile, created = UserProfile.objects.get_or_create(user=self.user)
            profile.is_online = is_online
            profile.last_seen = timezone.now()
            profile.save()
        except Exception:
            pass
