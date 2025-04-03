from django.db import models

class Request(models.Model):
    name = models.CharField(max_length=255, null=True)
    category = models.CharField(max_length=255, null=True)
    description = models.TextField()
    photo = models.ImageField(upload_to='request_photos/', blank=True, null=True)
    urgency = models.CharField(
        max_length=50,
        choices=[("висока", "Висока"), ("середня", "Середня"), ("низька", "Низька")]
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Очікує"), ("accepted", "Прийнятий"), ("rejected", "Відхилений")],
        default="pending"
    )

    def __str__(self):
        return self.name
