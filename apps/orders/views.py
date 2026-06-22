"""Views for checkout and order management."""
import uuid
from django.shortcuts import render,redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from apps.userprofile.models import Address
from apps.products.models import Cart
from .models import Order, OrderItem, OrderAddress
from django.db.models import Q

SHIPPING_CHARGES = {
    'standard': 0,
    'express': 25,
}

def generate_order_number():
    return 'ORD' + str(uuid.uuid4().hex[:8]).upper()

def handle_payment(payment_method, order):
    if payment_method == 'cod':
        order.order_status = 'pending'
        order.save()
        return True, "Order Placed Successfully"
    elif payment_method == 'card':
        return False, "Card payment not yet available."
    elif payment_method == 'upi':
        return False, "UPI payment not yet available."
    else:
        return False, "Invalid payment method."


@login_required
@never_cache
def checkout(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    cart, _ = Cart.objects.get_or_create(user=user)
    cart_items = cart.items.select_related('product_variant__product').all()

    subtotal = sum(item.total_price for item in cart_items)

    delivery_option = request.GET.get('delivery_option', 'standard')
    shipping_charge = SHIPPING_CHARGES.get(delivery_option, 0)
    total = subtotal + shipping_charge

    context = {
        'addresses': addresses,
        'default_address': default_address,
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'shipping_label': 'Free' if shipping_charge == 0 else f'₹{shipping_charge}',
        'total': total,
        'delivery_option': delivery_option,
    }
    return render(request, 'user/checkout.html', context)

@login_required
@never_cache
def place_order(request):
    if request.method == 'POST':
        user = request.user

        #get selected address
        address_id = request.POST.get('selected_address')
        if not address_id:
            messages.error(request,"Please select a delivery address")
            return redirect('checkout')

        address = get_object_or_404(Address, id=address_id, user=user)

        # 2. get delivery and payment details
        delivery_option = request.POST.get('delivery_option', 'standard')
        shipping_charge = SHIPPING_CHARGES.get(delivery_option, 0)
        payment_method = request.POST.get('payment_method', 'cod')

        # 3. get cart items
        cart = get_object_or_404(Cart, user=user)
        cart_items = cart.items.select_related('product_variant').all()

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        # 4. calculate totals
        total_amount = sum(item.total_price for item in cart_items)
        discount_amount = 0 # to be added later
        final_amount = total_amount + shipping_charge - discount_amount

        # 5. save address into OrderAddress
        order_address = OrderAddress.objects.create(
            user=user,
            full_name=address.full_name,
            phone_number=address.phone_number,
            address_line1=address.address_line1,
            address_line2=address.address_line2,
            city=address.city,
            state=address.state,
            country=address.country,
            pincode=address.pincode,
            address_type=address.address_type,
        )

        # 6. create order
        order = Order.objects.create(
            user=user,
            order_address=order_address,
            order_number=generate_order_number(),
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            payment_method=payment_method
        )

        # 7. create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_variant=item.product_variant,
                quantity=item.quantity,
                price=item.product_variant.effective_price,
                total=item.total_price,
            )

        # 8. handle payment
        success, message = handle_payment(payment_method, order)

        if success:
            cart_items.delete()
            messages.success(request, message)
            return redirect('order_confirmation', order_id=order.id)
        else:
            order.delete()
            order_address.delete()
            messages.error(request, message)
            return redirect('checkout')

    return redirect('checkout')

@login_required
@never_cache
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product_variant__product').all()

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'user/order_confirmation.html', context)

@login_required
@never_cache
def order_management(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort = request.GET.get('sort', '').strip()

    orders = Order.objects.select_related('user', 'order_address').order_by('-created_at')

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__full_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(order_address__phone_number__icontains=search_query)
        )

    if status_filter:
        orders = orders.filter(order_status=status_filter)

    if sort == 'date_old':
        orders = orders.order_by('created_at')
    elif sort == 'amount_high':
        orders = orders.order_by('-final_amount')
    elif sort == 'amount_low':
        orders = orders.order_by('final_amount')
    else:
        orders = orders.order_by('-created_at')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/order_management.html', {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort': sort,
        'status_choices': Order.STATUS_CHOICES,
    })

@login_required
@never_cache
def admin_order_detail(request, order_id):
    if not request.user.is_superuser:
        return redirect('admin_login')

    order = get_object_or_404(
        Order.objects.select_related('user', 'order_address'),
        id=order_id
    )

    order_items = order.items.select_related('product_variant__product').all()

    allowed_values = get_allowed_next_statuses(order.order_status)

    allowed_status_choices = [
        choice for choice in Order.STATUS_CHOICES
        if choice[0] in allowed_values
    ]

    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'status_choices': allowed_status_choices,
    })

def get_allowed_next_statuses(current_status):
    status_flow = {
        'pending': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered', 'cancelled'],
        'delivered': [],
        'cancelled': [],
    }

    return status_flow.get(current_status, [])

@login_required
@never_cache
def update_order_status(request, order_id):
    if not request.user.is_superuser:
        return redirect('admin_login')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        allowed_statuses = get_allowed_next_statuses(order.order_status)

        if new_status in allowed_statuses:
            order.order_status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')
        else:
            messages.error(request, 'Invalid status change. Please update order step by step.')

    return redirect('admin_order_detail', order_id=order.id)