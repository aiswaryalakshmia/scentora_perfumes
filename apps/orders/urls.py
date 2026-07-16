from django.urls import path
from . import views

urlpatterns = [

    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('admin-panel/orders/', views.order_management, name='order_management'),
    path('admin-panel/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('admin-panel/orders/<int:order_id>/items/<int:item_id>/status/', views.update_item_status, name='update_item_status'),
    path('admin-panel/orders/<int:order_id>/return/', views.handle_return_request, name='handle_return_request'),
    path('admin-panel/orders/<int:order_id>/item/<int:item_id>/return/', views.handle_item_return_request, name='handle_item_return_request'),
    path('payment/initiate/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/', views.verify_payment,   name='verify_payment'),
    path('payment/success/<int:order_id>/', views.payment_success,  name='payment_success'),
    path('payment/failure/<int:order_id>/', views.payment_failure,  name='payment_failure'),
    path('coupon/apply/', views.apply_coupon,  name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
    path('admin-panel/coupons/', views.coupon_management, name='coupon_management'),
    path('admin-panel/coupons/add/', views.add_coupon, name='add_coupon'),
    path('admin-panel/coupons/<int:coupon_id>/edit/', views.edit_coupon, name='edit_coupon'),
    path('admin-panel/coupons/<int:coupon_id>/toggle/', views.toggle_coupon_status,name='toggle_coupon_status'),
    path('admin-panel/coupons/<int:coupon_id>/delete/', views.delete_coupon, name='delete_coupon'),
    path('admin-panel/sales-report/', views.sales_report, name='sales_report'),
    path('admin-panel/sales-report/pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('admin-panel/sales-report/excel/', views.sales_report_excel, name='sales_report_excel'),
]
