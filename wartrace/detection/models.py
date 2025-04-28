from django.db import models
from django.conf import settings
from content.models import MarkerFile
import os
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile # Import ContentFile

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
    
    # The specific model that was used (e.g., 'yolo11m', 'yolo11s_military')
    model_name = models.CharField(max_length=100)
    
    # Summary of detection results (e.g., "Found 5 objects: 2 persons, 3 vehicles")
    summary = models.TextField(blank=True)
    
    # Path to the processed image (relative to MEDIA_URL) - Kept for backward compatibility
    image_path = models.CharField(max_length=255, blank=True, null=True) # Allow null
    
    # New field to store the processed image directly
    processed_image = models.FileField(upload_to='detection_results/', null=True, blank=True)
    
    # Optional metadata/attributes as JSON (inference time, settings used, etc.)
    metadata = models.JSONField(null=True, blank=True)
    
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
        # Prioritize the new FileField
        if self.processed_image and hasattr(self.processed_image, 'url'):
            try:
                return self.processed_image.url
            except ValueError:
                # Handle cases where the file might be missing or storage fails
                pass
        
        # Fallback to the old image_path for backward compatibility
        if self.image_path:
            path = self.image_path
            if path.startswith('/'):
                path = path[1:]
            # Construct URL using MEDIA_URL (assuming default filesystem storage for old files)
            # Note: This might need adjustment depending on how MEDIA_URL and storage were configured previously.
            try:
                # Check if the old path exists using default storage for robustness
                if default_storage.exists(path):
                     # Use storage URL method if possible, otherwise join manually
                    try:
                        return default_storage.url(path)
                    except NotImplementedError:
                         return os.path.join(settings.MEDIA_URL, path)
            except Exception:
                 # If storage check fails, fallback to simple join
                 return os.path.join(settings.MEDIA_URL, path)

        return None # No image available
    
    @property
    def is_object_detection(self):
        """Check if this is an object detection result"""
        return self.detector_type in ['object_detection', 'military_detection']
    
    @property
    def inference_time(self):
        """Return inference time from metadata if available"""
        if self.metadata and 'inference_time' in self.metadata:
            return self.metadata['inference_time']
        return None
    
    @property
    def total_objects(self):
        """Return the total number of detected objects"""
        return self.objects.count()
    
    @property
    def object_classes(self):
        """Return a dictionary of detected object classes with counts"""
        class_counts = {}
        for obj in self.objects.all():
            class_counts[obj.label] = class_counts.get(obj.label, 0) + 1
        return class_counts
    
    @property
    def parent_marker(self):
        """Return the parent marker"""
        return self.marker_file.marker if self.marker_file else None


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
    
    @property
    def is_military(self):
        """Check if this is a military object"""
        military_classes = [
            'camouflage_soldier', 'weapon', 'military_tank', 'military_truck', 
            'military_vehicle', 'soldier', 'military_artillery', 'trench', 
            'military_aircraft', 'military_warship'
        ]
        return self.label.lower() in military_classes


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
    
    # Threshold for detections (0-1)
    confidence_threshold = models.FloatField(default=0.25)
    
    # IOU threshold for non-maximum suppression (0-1)
    iou_threshold = models.FloatField(default=0.45)
    
    class Meta:
        ordering = ['order', 'detector_type']
    
    def __str__(self):
        return self.display_name
    
    @property
    def get_config(self):
        """Return the configuration as a dictionary"""
        return self.config if isinstance(self.config, dict) else {}
