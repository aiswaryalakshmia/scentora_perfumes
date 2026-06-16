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
    path('admin-panel/variant/toggle/<int:variant_id>/', views.toggle_variant_status, name='toggle_variant_status'),
    path('admin-panel/variant/<int:variant_id>/delete/', views.delete_variant, name='delete_variant'),
    path('admin-panel/variant-image/<int:image_id>/delete/',views.delete_variant_image,name="delete_variant_image"),
    path('shop/', views.shop, name='shop'),
    path('shop/product_details/<int:variant_id>/', views.product_details, name='product_details'),
    path('collections/' ,views.collections, name='collections'),
    path('collections/<int:category_id>/', views.collection_details, name='collection_details'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]