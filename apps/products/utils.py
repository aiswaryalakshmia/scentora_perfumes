from decimal import Decimal
from django.utils import timezone

def get_best_offer_for_variant(variant):
    """
    Checks product-level and category-level active offers.
    Returns the best (highest %) offer and its percentage.
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
    Applies whichever gives the customer a lower price (larger discount).

    Option A: effective_price kept for backward compatibility.
    This function is used everywhere going forward.

    Returns:
        final_price     — price customer actually pays
        discount_amount — total rupee discount applied
        offer_applied   — Offer object if offer won, else None
    """
    base_price = variant.price

    # Offer-based discount (percentage)
    best_offer, best_pct = get_best_offer_for_variant(variant)
    offer_discount = (base_price * best_pct / Decimal('100')) if best_pct > 0 else Decimal('0')

    # Manual discount (existing discount_price field on variant)
    manual_discount = variant.discount_price or Decimal('0')    

    # Apply whichever is larger — better deal for customer
    if offer_discount >= manual_discount:
        final_price     = base_price - offer_discount
        discount_amount = offer_discount
        offer_applied   = best_offer
    else:
        final_price     = base_price - manual_discount
        discount_amount = manual_discount
        offer_applied   = None   # manual discount won, no offer badge shown

    return final_price, discount_amount, offer_applied