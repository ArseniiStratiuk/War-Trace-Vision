from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    path('file/<int:file_id>/process/', views.process_single_file, name='process_file'),
    path('marker/<int:marker_id>/process/', views.process_marker_api, name='process_marker'),
    path('marker/<int:marker_id>/results/', views.marker_detection_results, name='marker_results'),
    path('review/', views.review_view, name='review'),
]
