"""Views for checkout and order management."""
import uuid
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from apps.userprofile.models import Address
from apps.products.models import Cart
from .models import Order, OrderItem, OrderAddress


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




