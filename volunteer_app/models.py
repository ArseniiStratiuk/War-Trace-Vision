#volunteer_app/models.py

from django.db import models
from authentication.models import UserProfile

class Request(models.Model):
    STATUS_CHOICES = [
        ('done', "Виконано"),
        ('in_progress', "Виконується"),
        ('in_search', "В пошуку"),
    ]

    URGENCY_CHOICES = [
        ("висока", "Висока"),
        ("середня", "Середня"),
        ("низька", "Низька"),
    ]

    author = models.ForeignKey(  # 🔄 Замість "user"
        UserProfile, on_delete=models.CASCADE, related_name='requests'
    )
    name = models.CharField(max_length=255, null=True)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_search')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, null=True, blank=True)
    volunteer = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='volunteer_req'
    )
    aproximate_price = models.IntegerField(verbose_name="Приблизна ціна", default=1)

    def __str__(self):
        return self.name


class VolunteerViewedRequest(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    req = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='viewed_requests')

    class Meta:
        unique_together = ('user', 'req')
