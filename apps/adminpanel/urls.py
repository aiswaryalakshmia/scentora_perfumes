from django.urls import path
from .import views

urlpatterns=[
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

]