from decimal import Decimal
from django.utils import timezone
from .models import Coupon, CouponUsage


def validate_coupon(code, user, cart_total):
    """
    Validates a coupon code for a given user and cart total.
    Returns (coupon, discount_amount, error_message)
    """
    # 1. Does coupon exist?
    try:
        coupon = Coupon.objects.get(coupon_code=code.strip().upper())
    except Coupon.DoesNotExist:
        return None, Decimal('0'), "Invalid coupon code."

    # 2. Is coupon active?
    if coupon.status != 'active':
        return None, Decimal('0'), "This coupon is no longer active."

    # 3. Has it expired?
    today = timezone.now().date()
    if today > coupon.expiry_date:
        return None, Decimal('0'), "This coupon has expired."

    # 4. Has usage limit been reached?
    if coupon.used_count >= coupon.usage_limit:
        return None, Decimal('0'), "This coupon has reached its usage limit."

    # 5. Has this user already used it?
    if CouponUsage.objects.filter(coupon=coupon, user=user).exists():
        return None, Decimal('0'), "You have already used this coupon."

    # 6. Is cart total above minimum price?
    if cart_total < coupon.minimum_price:
        return None, Decimal('0'), f"Minimum order amount of ₹{coupon.minimum_price} required for this coupon."

    # All checks passed
    discount = coupon.calculate_discount(cart_total)
    return coupon, discount, None