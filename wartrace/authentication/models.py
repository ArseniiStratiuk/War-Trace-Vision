from django.db import models
from django.contrib.auth.models import User
import json

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    CATEGORY_CHOICES = [
        ('soldier', 'Soldier'),
        ('volunteer', 'Volunteer'),
    ]
    category = models.CharField(max_length=9, choices=CATEGORY_CHOICES, blank=True, null=True)
    contacts = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.user.username)

    def get_contacts(self):
        if self.contacts:
            return json.loads(self.contacts)
        return {}

    def set_contacts(self, data):
        self.contacts = json.dumps(data)
