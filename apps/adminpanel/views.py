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
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from apps.orders.models import Order, OrderItem

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

    all_orders = Order.objects.exclude(order_status='cancelled')
    total_sales = all_orders.aggregate(total=Sum('final_amount'))['total'] or 0
    total_orders = all_orders.count()
    total_customers = User.objects.filter(is_superuser=False).count()
    revenue = all_orders.filter(payment_status='paid').aggregate(total=Sum('final_amount'))['total'] or 0

    chart_data = get_chart_data('monthly')

    best_products = (
        OrderItem.objects.filter(order__order_status__in=['delivered', 'shipped', 'processing'])
        .values('product_variant__product__product_name')
        .annotate(total_sold=Sum('quantity'), total_revenue=Sum('total'))
        .order_by('-total_sold')[:10]
    )

    best_categories = (
        OrderItem.objects.filter(order__order_status__in=['delivered', 'shipped', 'processing'])
        .values('product_variant__product__category__category_name')
        .annotate(total_sold=Sum('quantity'), total_revenue=Sum('total'))
        .order_by('-total_sold')[:10]
    )

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'revenue': revenue,
        'chart_labels': chart_data['labels'],
        'chart_values': chart_data['values'],
        'best_products': best_products,
        'best_categories': best_categories,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard.html', context)


def get_chart_data(period):
    today = timezone.now().date()

    if period == 'daily':
        start = today - timedelta(days=29)
        qs = (
            Order.objects.exclude(order_status='cancelled')
            .filter(created_at__date__gte=start)
            .annotate(period_group=TruncDate('created_at'))
            .values('period_group')
            .annotate(total=Sum('final_amount'))
            .order_by('period_group')
        )
        labels = [row['period_group'].strftime('%b %d') for row in qs]

    elif period == 'yearly':
        start = today.replace(year=today.year - 4, month=1, day=1)
        qs = (
            Order.objects.exclude(order_status='cancelled')
            .filter(created_at__date__gte=start)
            .annotate(period_group=TruncYear('created_at'))
            .values('period_group')
            .annotate(total=Sum('final_amount'))
            .order_by('period_group')
        )
        labels = [row['period_group'].strftime('%Y') for row in qs]

    else:
        start = (today.replace(day=1) - timedelta(days=365))
        qs = (
            Order.objects.exclude(order_status='cancelled')
            .filter(created_at__date__gte=start)
            .annotate(period_group=TruncMonth('created_at'))
            .values('period_group')
            .annotate(total=Sum('final_amount'))
            .order_by('period_group')
        )
        labels = [row['period_group'].strftime('%b %Y') for row in qs]

    values = [float(row['total'] or 0) for row in qs]
    return {'labels': labels, 'values': values}


@login_required
@never_cache
def dashboard_chart_data(request):
    if not request.user.is_superuser:
        return redirect('login')
    period = request.GET.get('period', 'monthly')
    data = get_chart_data(period)
    return JsonResponse(data)

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
