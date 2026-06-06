from django.urls import path
from . import views

urlpatterns = [

    path('admin-panel/categories/', views.category_management, name='category_management'),
    path('admin-panel/add_category/', views.add_category, name='add_category'),
    path('admin-panel/categories/<int:category_id>/edit', views.edit_category, name='edit_category'),
    path('admin-panel/categories/<int:category_id>/toggle-status', views.toggle_category_status, name='toggle_category_status'),
    path('admin-panel/products/', views.product_management, name='product_management'),
    path('admin-panel/add_product/', views.add_product, name='add_product'),
    path('admin-panel/product/add_variant/<int:product_id>/', views.add_variant, name="add_variant"),
    path('admin-panel/product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('admin-panel/product/<int:product_id>/toggle-status/', views.toggle_product_status, name='toggle_product_status'),
    path('admin-panel/variant/<int:variant_id>/update/', views.update_variant, name='update_variant'),
    path('admin-panel/variant/<int:variant_id>/delete/', views.delete_variant, name='delete_variant'),
]