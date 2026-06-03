from django.urls import path
from . import views

urlpatterns = [

    path('admin-panel/categories/', views.category_management, name='category_management'),
    path('admin-panel/add_category/', views.add_category,name='add_category')
]