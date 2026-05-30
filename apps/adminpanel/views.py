from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.authentication.models import User
from django.contrib.auth import logout

def admin_login(request):
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
def admin_dashboard(request):
    return render(request,'admin_dashboard.html')

@login_required
def user_management(request):

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
        "page_obj": page_obj,
        "search_query": search_query
    })

def toggle_user_status(request,user_id):
    user = get_object_or_404(
        User,
        id=user_id
    )

     # prevent blocking admin
    if not user.is_superuser:

        user.is_active = not user.is_active

        user.save()

    return redirect('user_management')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')