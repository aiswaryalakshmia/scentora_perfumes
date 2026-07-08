from decimal import Decimal
from django.utils import timezone
from .models import Coupon, CouponUsage


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