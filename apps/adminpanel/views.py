"""
Admin configurations for the application.
"""
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from apps.authentication.models import User

@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        user=authenticate(
            request,
            username=email,
            password=password
        )
        if user is not None and user.is_superuser:
            login(request,user)
            return redirect('admin_dashboard')
        else:
            messages.error(
                request,
                'Invalid admin credentials'
            )
    return render(request,'admin_login.html')

@login_required
@never_cache
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')
    return render(request,'admin_dashboard.html')

@login_required
@never_cache
def user_management(request):
    if not request.user.is_superuser:
        return redirect('login')

    search_query=request.GET.get('search','')
    users=User.objects.all().order_by('-created_at')
    if search_query:
        users = users.filter(
            Q(full_name__icontains=search_query) | Q(email__icontains=search_query)
        )

    paginator = Paginator(users, 5)  # 5 users per page
    page_number = request.GET.get('page')  # ?page=2
    page_obj = paginator.get_page(page_number)

    return render(request, "user_management.html", {
        "users": page_obj,
        "search_query": search_query
    })

def toggle_user_status(request,user_id):
    if not request.user.is_superuser:
        return redirect('login')

    user = get_object_or_404(
        User,
        id=user_id
    )

     # prevent blocking admin
    if not user.is_superuser:
        user.is_active = not user.is_active
        user.save()

    if user.is_active:
            messages.success(request, f"{user.full_name} has been unblocked")
    else:
            messages.success(request, f"{user.full_name} has been blocked")    

    return redirect('user_management')

@never_cache
def admin_logout(request):
    logout(request)
    return redirect('admin_login')
