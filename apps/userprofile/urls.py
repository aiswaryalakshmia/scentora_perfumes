from django.urls import path
from . import views

urlpatterns = [
    path('profile/dashboard/', views.profile_dashboard, name='profile_dashboard'),
    path('profile/addressbook/',views.address_book,name='address_book'),
    path('profile/addressbook/add/', views.add_address, name='add_address'),
    path('profile/addressbook/delete/<int:address_id>',views.delete_address,name='delete_address'),
    path('profile/address_book/edit/<int:address_id>',views.edit_address,name='edit_address'),
    path('profile/edit_profile/',views.edit_profile,name='edit_profile'),
    path('address/set-default/<int:address_id>/',views.set_default_address,name='set_default_address'),
    path('profile/my-orders/', views.my_orders, name='my_orders'),
    path('profile/my-orders/<int:order_id>/', views.order_detail, name='order_detail')
    ]
