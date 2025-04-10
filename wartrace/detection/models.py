from django.db import models
from authentication.models import User

class DetectionType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Detection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections')
    image = models.ImageField(upload_to='detections/')
    detection_type = models.ForeignKey(DetectionType, on_delete=models.SET_NULL, null=True,
                                       related_name='detections')
    coordinates = models.JSONField(null=True, blank=True)  # Store detection coordinates
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Detection by {self.user.username} - {self.created_at}"
