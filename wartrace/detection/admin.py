from django.contrib import admin
from .models import Detection, ObjectDetection, ClassificationResult, SegmentationMask

class ObjectDetectionInline(admin.TabularInline):
    model = ObjectDetection
    extra = 0

class ClassificationResultInline(admin.TabularInline):
    model = ClassificationResult
    extra = 0

class SegmentationMaskInline(admin.TabularInline):
    model = SegmentationMask
    extra = 0

@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'detector_type', 'model_name', 'marker_file', 'created_at']
    list_filter = ['detector_type', 'model_name', 'created_at']
    search_fields = ['marker_file__marker__title', 'detector_type']
    inlines = [ObjectDetectionInline, ClassificationResultInline, SegmentationMaskInline]
