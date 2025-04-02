from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Marker(models.Model):
    CATEGORY_CHOICES = [
        ('military', 'Military'),
        ('infrastructure', 'Infrastructure'),
        ('residential', 'Residential'),
        ('hazard', 'Hazard'),
        ('other', 'Other'),
    ]
    
    VERIFICATION_CHOICES = [
        ('verified', 'Verified'),
        ('unverified', 'Unverified'),
        ('ai-detected', 'AI Detected'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('verified_only', 'Verified Users Only'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='markers')
    title = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    verification = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='unverified')
    confidence = models.IntegerField(default=0)  # Stored as percentage 0-100
    source = models.CharField(max_length=255, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Detection options
    object_detection = models.BooleanField(default=False)
    camouflage_detection = models.BooleanField(default=False)
    request_verification = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.latitude}, {self.longitude})"

class MarkerFile(models.Model):
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='user_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"File for {self.marker.title}"
