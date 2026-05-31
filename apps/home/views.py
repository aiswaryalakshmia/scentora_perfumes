from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

@never_cache
def home(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'home.html')
