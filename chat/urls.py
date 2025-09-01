# chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'


urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('start/<int:request_id>/', views.start_chat, name='start_chat'),
    path('<int:chat_id>/', views.chat_detail, name='chat_detail'),
]
