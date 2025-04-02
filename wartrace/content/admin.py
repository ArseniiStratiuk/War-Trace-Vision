from django.contrib import admin
from .models import Marker, MarkerFile

class MarkerFileInline(admin.TabularInline):
    model = MarkerFile
    extra = 1

@admin.register(Marker)
class MarkerAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'verification', 'user', 'date', 'visibility')
    list_filter = ('category', 'verification', 'visibility', 'date')
    search_fields = ('title', 'description', 'user__username')
    inlines = [MarkerFileInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'user')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Categorization', {
            'fields': ('category', 'verification', 'confidence', 'source')
        }),
        ('Timing', {
            'fields': ('date',)
        }),
        ('Options', {
            'fields': ('visibility', 'object_detection', 'camouflage_detection', 'request_verification')
        }),
    )

@admin.register(MarkerFile)
class MarkerFileAdmin(admin.ModelAdmin):
    list_display = ('marker', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('marker__title',)
