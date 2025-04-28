import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            message_text = data['message']
            
            # Save message to database
            message = await self.save_message(message_text)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_text,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'timestamp': message['timestamp'],
                    'message_id': message['id']
                }
            )
        elif message_type == 'typing':
            # Send typing indicator to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'sender_id': self.user.id,
                    'is_typing': data['is_typing']
                }
            )
        elif message_type == 'read':
            # Mark messages as read
            await self.mark_messages_read()
            
            # Send read receipt
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'reader_id': self.user.id,
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'is_typing': event['is_typing']
        }))
    
    async def read_receipt(self, event):
        # Send read receipt to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read',
            'reader_id': event['reader_id']
        }))
    
    @database_sync_to_async
    def save_message(self, message_text):
        # Get the chat
        chat = Chat.objects.get(id=self.chat_id)
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            sender=self.user,
            text=message_text,
            is_read=False
        )
        
        # Update chat last activity
        chat.save()  # This will update the auto_now updated_at field
        
        return {
            'id': message.id,
            'timestamp': message.timestamp.strftime('%H:%M')
        }
    
    @database_sync_to_async
    def mark_messages_read(self):
        # Mark all messages in this chat from other users as read
        Message.objects.filter(
            chat_id=self.chat_id,
            is_read=False
        ).exclude(
            sender=self.user
        ).update(is_read=True)