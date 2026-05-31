from django.shortcuts import render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def home(request):
    return render(request, 'home.html')