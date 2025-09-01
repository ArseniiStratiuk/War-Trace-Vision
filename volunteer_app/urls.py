#volunteer_app/urls.py
from django.urls import path, include
from . import views

app_name = 'volunteer_app'

urlpatterns = [
    path('chat/', include('chat.urls')),
    path('', views.request_list, name='search'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('start-chat/<int:request_id>/', views.start_chat_and_redirect, name='start_chat_and_redirect'),
    path('chat-history/', views.chat_history, name='chat_history'),
]
