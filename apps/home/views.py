from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from apps.products.models import Category,ProductVariant
from apps.products.utils import get_offer_price


@never_cache
def home(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    categories = Category.objects.filter(status='active')

    new_arrivals = ProductVariant.objects.filter(
        status='active',
        product__status='active',
        product__category__status='active',
        stock__gt=0
    ).select_related(
        'product',
        'product__category'
    ).prefetch_related(
        'images'
    ).order_by('-created_at')[:4]

    for v in new_arrivals:
        fp, _, _ = get_offer_price(v)
        v.final_price = fp

    return render(request, 'home.html', {
        'categories': categories,
        'new_arrivals': new_arrivals,
    })
