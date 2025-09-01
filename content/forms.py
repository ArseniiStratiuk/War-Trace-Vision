from django import forms
from .models import Marker, MarkerFile

class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        fields = [
            'title', 
            'description', 
            'latitude', 
            'longitude', 
            'date', 
            'category', 
            'source', 
            'visibility',
            'object_detection',
            'camouflage_detection',
            'request_verification',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class MarkerFileForm(forms.ModelForm):
    class Meta:
        model = MarkerFile
        fields = ['file']
