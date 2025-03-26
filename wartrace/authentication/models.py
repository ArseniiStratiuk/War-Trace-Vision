from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Role(models.Model):
    SOLDIER = 'soldier'
    VOLUNTEER = 'volunteer'
    ANALYST = 'analyst'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (SOLDIER, 'Soldier'),
        (VOLUNTEER, 'Volunteer'),
        (ANALYST, 'Analyst'),
        (ADMIN, 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_type_display()}"

    def get_role_type_display(self):
        return self.role_type.capitalize()
