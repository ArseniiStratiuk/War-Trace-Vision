from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views # import auth views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('login/', views.user_login, name='login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'), #add password reset
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('logout/', views.user_logout, name='logout'), #add logout
    path('personal/', views.personal_page, name='personal_page'),
    path('bad_category/', views.bad_category, name='bad_category'),
    path('profile/<int:volunteer_id>', views.profile, name='profile'),
    path('submit/<int:req_id>', views.req_ready, name="req_ready"),
    path('settings/', views.settings, name='settings'),
    path('change_category/', views.add_second_category, name='change_category')
]
