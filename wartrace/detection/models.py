from django.db import models
from django.contrib.auth.models import User
from content.models import Marker, MarkerFile

class Detection(models.Model):
    """Main detection model to store analysis results for a file"""
    marker_file = models.ForeignKey(MarkerFile, on_delete=models.CASCADE, related_name='detections')
    detector_type = models.CharField(max_length=100)  # e.g. 'object_detection', 'military_detection'
    model_name = models.CharField(max_length=255)  # Name of the model used
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Summary fields
    summary = models.TextField(blank=True, null=True)  # Text summary of detection results
    image_path = models.CharField(max_length=255, null=True, blank=True)  # Path to result image if generated
    
    def __str__(self):
        return f"{self.detector_type} on {self.marker_file}"

    class Meta:
        ordering = ['-created_at']

class ObjectDetection(models.Model):
    """Stores individual object detection results (bounding boxes)"""
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='objects')
    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    x_min = models.FloatField()
    y_min = models.FloatField()
    x_max = models.FloatField()
    y_max = models.FloatField()
    
    def __str__(self):
        return f"{self.label} ({self.confidence:.2f})"

class ClassificationResult(models.Model):
    """Stores classification results"""
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='classifications')
    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    
    def __str__(self):
        return f"{self.label} ({self.confidence:.2f})"

class SegmentationMask(models.Model):
    """Stores segmentation mask results"""
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='masks')
    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    mask_path = models.CharField(max_length=255)  # Path to segmentation mask image
    
    def __str__(self):
        return f"{self.label} mask ({self.confidence:.2f})"
