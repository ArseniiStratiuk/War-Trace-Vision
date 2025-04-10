from django.urls import path
from . import views

urlpatterns = [
    path('', views.request_list, name='search'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
]
