from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    # Marker-level endpoints
    path('markers/<int:marker_id>/process/', views.process_marker_view, name='process_marker'),
    path('markers/<int:marker_id>/results/', views.marker_detection_results, name='marker_results'),
    path('markers/<int:marker_id>/status/', views.marker_processing_status, name='marker_processing_status'),
    
    # File-level endpoints
    path('files/<int:file_id>/process/', views.process_file_view, name='process_file'),
    path('files/<int:file_id>/results/', views.file_detection_results, name='file_results'),
    
    # API endpoints
    path('api/markers/<int:marker_id>/process/', views.process_marker_api, name='process_marker_api'),
    path('api/markers/<int:marker_id>/auto-process/', views.auto_process_marker, name='auto_process_marker'),
]
