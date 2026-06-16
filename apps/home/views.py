from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from apps.products.models import Category

@never_cache
def home(request):
    categories = Category.objects.filter(status='active')
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'home.html',{
        'categories':categories
    })
