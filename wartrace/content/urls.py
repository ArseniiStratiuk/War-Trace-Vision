from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('marker/create/', views.marker_create_view, name='marker_create'),
    path('marker/<int:pk>/', views.marker_detail_view, name='marker_detail'),
    path('annotation/create/', views.annotation_create_view, name='annotation_create'),
]
