from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    path('review/', views.review_view, name='review'),
]
