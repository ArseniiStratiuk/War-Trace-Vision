from django.db import models
from authentication.models import User
from maps.models import Area


class Marker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='markers')
    title = models.CharField(max_length=100)
    description = models.TextField()
    coordinates = models.JSONField()  # Store marker coordinates
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, related_name='markers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.marker.title}"


class Annotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='annotations')
    content = models.TextField()
    coordinates = models.JSONField(null=True, blank=True)  # For specific area annotations
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Annotation by {self.user.username} on {self.marker.title}"


class Verification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE, related_name='verifications')
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verification by {self.user.username} on {self.marker.title}"
