from django.urls import path
from . import views

urlpatterns = [

    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('admin-panel/orders/', views.order_management, name='order_management'),
    path('admin-panel/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
]
