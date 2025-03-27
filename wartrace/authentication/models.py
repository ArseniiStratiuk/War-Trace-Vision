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
    request_data = models.TextField(blank=True, null=True)
    contacts = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_request_data(self):
        if self.request_data:
            return json.loads(self.request_data)
        return {}

    def set_request_data(self, data):
        self.request_data = json.dumps(data)

    def get_contacts(self):
        if self.contacts:
            return json.loads(self.contacts)
        return {}

    def set_contacts(self, data):
        self.contacts = json.dumps(data)