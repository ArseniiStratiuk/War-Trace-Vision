from django.db import models
from django.conf import settings
from content.models import MarkerFile
import os

class Detection(models.Model):
    """
    Represents an AI detection result associated with a marker file.
    Each detection corresponds to one analysis of one file with one specific detector type.
    """
    # Link to the marker file that was processed
    marker_file = models.ForeignKey(
        MarkerFile, 
        on_delete=models.CASCADE, 
        related_name='detections'
    )
    
    # Type of detection performed (object_detection, military_detection, etc.)
    detector_type = models.CharField(max_length=50)
    
    # The specific model that was used (e.g., 'yolo11m', 'xbd_classifier')
    model_name = models.CharField(max_length=100)
    
    # Summary of detection results (e.g., "Found 5 objects: 2 persons, 3 vehicles")
    summary = models.TextField(blank=True)
    
    # Path to the processed image (relative to MEDIA_URL)
    image_path = models.CharField(max_length=255, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure we don't process the same file with the same detector type multiple times
        unique_together = ('marker_file', 'detector_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.detector_type} detection for {self.marker_file}"
    
    @property
    def image_url(self):
        """Return the full URL to the processed image"""
        if not self.image_path:
            return None
        
        # Remove leading slash if present to make path joining work correctly
        path = self.image_path
        if path.startswith('/'):
            path = path[1:]
            
        return os.path.join(settings.MEDIA_URL, path)
    
    @property
    def is_object_detection(self):
        """Check if this is an object detection result"""
        return self.detector_type in ['object_detection', 'military_detection']
    
    @property
    def is_classification(self):
        """Check if this is a classification result"""
        return self.detector_type in ['damage_assessment', 'emergency_recognition']


class ObjectDetection(models.Model):
    """
    Represents a single object detected in an image.
    Each Detection can have multiple ObjectDetections (e.g., multiple people, vehicles).
    """
    # Link to the parent detection
    detection = models.ForeignKey(
        Detection, 
        on_delete=models.CASCADE, 
        related_name='objects'
    )
    
    # Object label/class (e.g., 'person', 'car', 'tank')
    label = models.CharField(max_length=100)
    
    # Confidence score (0-1) of the detection
    confidence = models.FloatField()
    
    # Bounding box coordinates (x_min, y_min, x_max, y_max)
    x_min = models.FloatField()
    y_min = models.FloatField()
    x_max = models.FloatField()
    y_max = models.FloatField()
    
    # Optional metadata/attributes
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence']
    
    def __str__(self):
        return f"{self.label} ({self.confidence:.2f})"
    
    @property
    def area(self):
        """Calculate bounding box area"""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    @property
    def width(self):
        """Calculate bounding box width"""
        return self.x_max - self.x_min
    
    @property
    def height(self):
        """Calculate bounding box height"""
        return self.y_max - self.y_min
    
    @property
    def center_x(self):
        """Calculate bounding box center X coordinate"""
        return (self.x_min + self.x_max) / 2
    
    @property
    def center_y(self):
        """Calculate bounding box center Y coordinate"""
        return (self.y_min + self.y_max) / 2


class ClassificationResult(models.Model):
    """
    Represents a classification result.
    Each Detection can have multiple ClassificationResults for multi-class problems.
    """
    # Link to the parent detection
    detection = models.ForeignKey(
        Detection, 
        on_delete=models.CASCADE, 
        related_name='classifications'
    )
    
    # Class label (e.g., 'damaged', 'fire', 'flood')
    label = models.CharField(max_length=100)
    
    # Confidence score (0-1) of the classification
    confidence = models.FloatField()
    
    # Optional metadata/attributes
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence']
    
    def __str__(self):
        return f"{self.label} ({self.confidence:.2f})"


class SegmentationMask(models.Model):
    """
    Represents a segmentation mask for pixel-level predictions.
    """
    # Link to the parent detection
    detection = models.ForeignKey(
        Detection, 
        on_delete=models.CASCADE, 
        related_name='segmentation_masks'
    )
    
    # Class label that this mask represents
    label = models.CharField(max_length=100)
    
    # Path to the segmentation mask image
    mask_path = models.CharField(max_length=255)
    
    # Confidence score (0-1) of the segmentation
    confidence = models.FloatField()
    
    # Optional metadata/attributes
    metadata = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.label} mask for {self.detection}"
    
    @property
    def mask_url(self):
        """Return the full URL to the mask image"""
        if not self.mask_path:
            return None
            
        # Remove leading slash if present to make path joining work correctly
        path = self.mask_path
        if path.startswith('/'):
            path = path[1:]
            
        return os.path.join(settings.MEDIA_URL, path)


class DetectionConfig(models.Model):
    """
    Stores configuration information about available detection models.
    This allows for dynamic model configuration through the admin interface.
    """
    # Type of detector (object_detection, military_detection, etc.)
    detector_type = models.CharField(max_length=50, unique=True)
    
    # Display name for the UI
    display_name = models.CharField(max_length=100)
    
    # Description of what this detector does
    description = models.TextField(blank=True)
    
    # Icon class or path for UI rendering
    icon = models.CharField(max_length=100, blank=True)
    
    # Whether this detector is enabled in the system
    is_enabled = models.BooleanField(default=True)
    
    # Order for display in UI
    order = models.IntegerField(default=0)
    
    # Configuration options for this detector type (stored as JSON)
    config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['order', 'detector_type']
    
    def __str__(self):
        return self.display_name
