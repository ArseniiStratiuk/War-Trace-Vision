from django.contrib import admin
from .models import Marker, MarkerFile, Comment

class MarkerFileInline(admin.TabularInline):
    model = MarkerFile
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Marker)
class MarkerAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'verification', 'user', 'date', 'visibility')
    list_filter = ('category', 'verification', 'visibility', 'date')
    search_fields = ('title', 'description', 'user__username')
    inlines = [MarkerFileInline, CommentInline]
    
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

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('marker', 'user', 'text_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('marker__title', 'user__username', 'text')
    
    def text_preview(self, obj):
        # Return first 50 characters of comment text
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    
    text_preview.short_description = 'Comment'
