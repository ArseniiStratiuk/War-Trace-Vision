from django.urls import path
from . import views

urlpatterns = [
    path('marker/create/', views.marker_create, name='marker_create'),
    path('marker/<int:pk>/', views.marker_detail, name='marker_detail'),
    path('api/markers/', views.marker_api, name='marker_api'),
]
