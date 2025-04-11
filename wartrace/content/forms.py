from django import forms
from .models import Marker, MarkerFile, Comment

class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        fields = [
            'title', 'description', 'latitude', 'longitude', 
            'date', 'category', 'source', 'verification',
            'visibility', 'object_detection', 'military_detection',
            'damage_assessment', 'emergency_recognition',
            'request_verification'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class MarkerFileForm(forms.ModelForm):
    class Meta:
        model = MarkerFile
        fields = ['file']
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
