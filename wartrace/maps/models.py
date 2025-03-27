from django.db import models


class MapLayer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=100)
    coordinates = models.JSONField()  # Store GeoJSON or coordinates
    layer = models.ForeignKey(MapLayer, on_delete=models.CASCADE, related_name='areas')

    def __str__(self):
        return self.name
