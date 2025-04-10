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

    author = models.ForeignKey("authentication.UserProfile", on_delete=models.CASCADE, related_name='requests')
    name = models.CharField(max_length=255, null=True)
    description = models.TextField()
    aproximate_price = models.IntegerField(verbose_name="Приблизна ціна", default=1)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    urgency = models.CharField(max_length=20,choices=URGENCY_CHOICES)

    volunteer = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='volunteer_req'
    )


    def __str__(self):
        return str(self.name)

class VolunteerViewedRequest(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_index=True)
    req = models.ForeignKey('volunteer_app.Request', on_delete=models.CASCADE, db_index=True, related_name="viewed_requests")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'req'], name='unique_user_req')
        ]
