from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # ваші інші маршрути
    path('', views.request_list, name='home'),
    path('map/', views.map_view, name='map'),
    path('chat/', views.chat_list, name='chat'),
    path('profile/', views.profile, name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
