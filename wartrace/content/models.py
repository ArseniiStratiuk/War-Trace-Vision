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
        ('disputed', 'Disputed'),
        ('pending', 'Pending'),
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
    confidence = models.IntegerField(default=100)  # Stored as percentage 0-100
    source = models.CharField(max_length=255, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Detection options
    object_detection = models.BooleanField(default=False)
    military_detection = models.BooleanField(default=False)  # New field for military object detection
    damage_assessment = models.BooleanField(default=False)
    emergency_recognition = models.BooleanField(default=False)  # New field for emergency recognition
    request_verification = models.BooleanField(default=False)
    
    # Add upvoting functionality
    upvotes = models.ManyToManyField(User, related_name='marker_upvotes', blank=True)
    
    @property
    def upvote_count(self):
        return self.upvotes.count()

    def __str__(self):
        return f"{self.title} ({self.latitude}, {self.longitude})"

class MarkerFile(models.Model):
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='user_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"File for {self.marker.title}"

class Comment(models.Model):
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.ManyToManyField(User, related_name='comment_upvotes', blank=True)
    
    @property
    def votes(self):
        return self.upvotes.count()
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.marker.title}"

class MarkerReport(models.Model):
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Report on {self.marker.title} by {self.user.username}"
