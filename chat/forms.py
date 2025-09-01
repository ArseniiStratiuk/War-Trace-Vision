# chat/forms.py
from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'message-input',
                'placeholder': 'Напишіть повідомлення...',
                'rows': 3
            })
        }