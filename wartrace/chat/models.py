# chat/models.py

from django.db import models
from django.contrib.auth import get_user_model
from volunteer_app.models import Request

User = get_user_model()

class Chat(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='chats')
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat for request '{self.request}'"
    
    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender}: {self.text[:30]}"