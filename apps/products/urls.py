from django.urls import path
from . import views

urlpatterns = [

    path('admin-panel/categories/', views.category_management, name='category_management'),
    path('admin-panel/add_category/', views.add_category, name='add_category'),
    path('admin-panel/categories/<int:category_id>/edit', views.edit_category, name='edit_category'),
    path('admin-panel/categories/<int:category_id>/toggle-status', views.toggle_category_status, name='toggle_category_status'),
    path('admin-panel/products/', views.product_management, name='product_management'),
    path('admin-panel/add_product/', views.add_product, name='add_product'),
    path('admin-panel/product/<int:product_id>/', views.product_details, name="product_details"),
]