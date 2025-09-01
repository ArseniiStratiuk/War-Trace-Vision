from django import forms
from .models import Request

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            'name',
            'description',
            'aproximate_price',
            'urgency',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'aproximate_price': forms.NumberInput(attrs={'min': 0}),
            'status': forms.Select(choices=Request.STATUS_CHOICES),
            'urgency': forms.Select(choices=Request.URGENCY_CHOICES),
        }
        labels = {
            'name':"Заголовок",
            'description': "Опис",
            'aproximate_price': "Приблизна ціна (грн)",
            'status': "Статус",
            'urgency': "Терміновість",
        }
