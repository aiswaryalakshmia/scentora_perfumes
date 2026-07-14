from decimal import Decimal
from django.utils import timezone
from .models import Coupon, CouponUsage, Order
from django.db.models import Sum


def validate_coupon(code, user, cart_total):    
    # Checks if coupon exist
    try:
        coupon = Coupon.objects.get(coupon_code=code.strip().upper())
    except Coupon.DoesNotExist:
        return None, Decimal('0'), "Invalid coupon code."

    # Check if coupon is active
    if coupon.status != 'active':
        return None, Decimal('0'), "This coupon is no longer active."

    # Check if it is expired
    today = timezone.now().date()
    if today > coupon.expiry_date:
        return None, Decimal('0'), "This coupon has expired."

    # Check usage limit been reached
    if coupon.used_count >= coupon.usage_limit:
        return None, Decimal('0'), "This coupon has reached its usage limit."

    # Check if user already used it
    if CouponUsage.objects.filter(coupon=coupon, user=user).exists():
        return None, Decimal('0'), "You have already used this coupon."

    # Is cart total above minimum price
    if cart_total < coupon.minimum_price:
        return None, Decimal('0'), f"Minimum order amount of ₹{coupon.minimum_price} required for this coupon."

    # If all checks passed
    discount = coupon.calculate_discount(cart_total)
    return coupon, discount, None

def release_abandoned_razorpay_orders(user):
    
    abandoned_orders = Order.objects.filter(
        user=user,
        payment_method='razorpay',
        payment_status='pending',
        order_status='pending',
    )

    for order in abandoned_orders:
        # restore stock
        for item in order.items.select_related('product_variant').all():
            item.product_variant.stock += item.quantity
            item.product_variant.save()

        # roll back coupon usage if one was applied
        if order.coupon:
            CouponUsage.objects.filter(coupon=order.coupon, user=order.user).delete()
            order.coupon.used_count = max(0, order.coupon.used_count - 1)
            order.coupon.save()

        order.order_status = 'cancelled'
        order.save()

        if hasattr(order, 'payment_detail'):
            order.payment_detail.mark_failed()

def calculate_item_refund(item):
    """
    Returns refund amount for one OrderItem, deducting its proportional
    share of the order-level coupon discount. Offer/manual discount is
    already baked into item.total.
    """
    order = item.order
    items_total = order.items.aggregate(total=Sum('total'))['total'] or Decimal('0')

    if items_total > 0:
        proportion = item.total / items_total
    else:
        proportion = Decimal('0')

    coupon_share = (order.coupon_discount or Decimal('0')) * proportion
    refund = item.total - coupon_share

    if refund < 0:
        refund = Decimal('0')

    return refund.quantize(Decimal('0.01'))
