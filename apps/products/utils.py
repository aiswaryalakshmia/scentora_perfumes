from decimal import Decimal
from django.utils import timezone
from apps.orders.models import OrderItem
from apps.products.models import Review

def get_best_offer_for_variant(variant):
    """
    Checks product-level and category-level active offers.
    Returns the best offer and its percentage.
    """
    today = timezone.now().date()
    best_pct   = Decimal('0')
    best_offer = None

    # Check product-specific offers
    for offer in variant.product.offers.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today,
    ):
        if offer.discount_percentage > best_pct:
            best_pct   = offer.discount_percentage
            best_offer = offer

    # Check category offers
    for offer in variant.product.category.offers.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today,
    ):
        if offer.discount_percentage > best_pct:
            best_pct   = offer.discount_percentage
            best_offer = offer

    return best_offer, best_pct


def get_offer_price(variant):
    """
    Returns final price after applying best available discount.
    Compares offer-based % discount vs existing manual discount_price.
    Applies whichever gives the customer a lower price (larger discount)    
    """
    base_price = variant.price

    # Offer-based discount (percentage)
    best_offer, best_pct = get_best_offer_for_variant(variant)
    offer_discount = (base_price * best_pct / Decimal('100')) if best_pct > 0 else Decimal('0')

    # Manual discount (existing discount_price field on variant)
    manual_discount = variant.discount_price or Decimal('0')    

    # Apply whichever is larger
    if offer_discount >= manual_discount:
        final_price     = base_price - offer_discount
        discount_amount = offer_discount
        offer_applied   = best_offer
    else:
        final_price     = base_price - manual_discount
        discount_amount = manual_discount
        offer_applied   = None   # manual discount won, no offer badge shown

    return final_price, discount_amount, offer_applied

def can_review_product(user, product):
    """
    Returns True if user has a delivered order containing this product
    and hasn't already reviewed it.
    """
    if not user.is_authenticated:
        return False

    has_delivered = OrderItem.objects.filter(
        order__user=user,
        order__order_status='delivered',
        product_variant__product=product,
    ).exists()

    if not has_delivered:
        return False

    already_reviewed = Review.objects.filter(user=user, product=product).exists()
    return not already_reviewed