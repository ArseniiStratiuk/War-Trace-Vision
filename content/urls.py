from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Marker CRUD operations
    path('marker/create/', views.create_marker_view, name='create_marker_view'),
    path('marker/create/submit/', views.create_marker, name='create_marker'),
    path('marker/<int:marker_id>/', views.marker_detail, name='marker_detail'),
    path('marker/<int:marker_id>/edit/', views.edit_marker_view, name='edit_marker'),
    path('marker/<int:marker_id>/edit/submit/', views.edit_marker_submit, name='edit_marker_submit'),
    path('marker/<int:marker_id>/delete/', views.delete_marker, name='delete_marker'),
    
    # Marker media and comment endpoints
    path('markers/<int:marker_id>/add-media/', views.add_media, name='add_media'),
    path('markers/<int:marker_id>/add-comment/', views.add_comment, name='add_comment'),
    path('marker/<int:marker_id>/delete-media/<int:file_id>/', views.delete_media, name='delete_media'),
    
    # Marker actions
    path('api/markers/<int:marker_id>/verify/', views.verify_marker, name='verify_marker'),
    path('markers/<int:marker_id>/upvote/', views.upvote_marker, name='upvote_marker'),
    path('api/markers/<int:marker_id>/report/', views.report_marker, name='report_marker'),
    
    # API endpoints
    path('api/markers/', views.marker_api, name='marker_api'),
    path('api/comments/<int:comment_id>/upvote/', views.upvote_comment, name='upvote_comment'),
]
