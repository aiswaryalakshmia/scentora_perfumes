"""
Allow logged-in users to update profile details and securely
change their password using OTP verification.
"""
import random
import re
from django.shortcuts import render,redirect
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from apps.authentication.models import User, OTP
from apps.products.models import Wishlist
from apps.orders.models import Order,OrderItem
from .models import Address
from apps.userprofile.wallet_utils import credit_wallet, has_been_refunded
from apps.userprofile.wallet_utils import get_wallet_balance
from apps.userprofile.models import WalletTransaction
from django.core.paginator import Paginator
from apps.products.utils import can_review_product
from apps.products.models import Review
from apps.authentication.validators import validate_password
from apps.orders.utils import calculate_item_refund
from apps.userprofile.wallet_utils import has_item_been_refunded

@login_required
@never_cache
def profile_dashboard(request):
    user = request.user
    orders = Order.objects.filter(user=user)

    recent_orders = orders.select_related('order_address').prefetch_related(
        'items__product_variant__product',
        'items__product_variant__images'
    ).order_by('-created_at')[:5]

    context = {
        'current_user': user,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(order_status='pending').count(),
        'wishlist_count': Wishlist.objects.filter(user=user).count(),
        'wallet_balance': get_wallet_balance(user),
        'recent_orders': recent_orders,
    }
    return render(request, 'userprofile.html', context)

@login_required
@never_cache   
def address_book(request):
    addresses = Address.objects.filter(user=request.user)
    context = {
          'addresses':addresses
     }
    return render(request,'address_book.html',context)

@login_required
@never_cache
def add_address(request):
    if request.method == 'POST':
        form_data = get_address_form_data(request)
        error = validate_address_data(form_data)

        if error:
            return render(
                request,
                'add_address.html',
                address_form_context(request, error)
            )

        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=form_data['full_name'],
            phone_number=form_data['phone_number'],
            address_line1=form_data['address_line1'],
            address_line2=form_data['address_line2'],
            city=form_data['city'],
            state=form_data['state'],
            country=form_data['country'],
            pincode=form_data['pincode'],
            address_type=form_data['address_type'],
            is_default=True if request.POST.get('is_default') else False
        )

        messages.success(request, "Address added successfully!")

        next_page = request.POST.get('next', '')
        if next_page == 'checkout':
            return redirect('checkout')

        return redirect('address_book')

    return render(
        request,
        'add_address.html',
        address_form_context(request)
    )

@login_required
@never_cache
def set_default_address(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    Address.objects.filter(
        user=request.user
    ).update(is_default=False)

    address.is_default = True
    address.save()

    return redirect('address_book')

@login_required
@never_cache
def delete_address(request,address_id):
    address=get_object_or_404(
        Address,
        user=request.user,
        id=address_id
    )

    address.delete()
    next_page = request.GET.get('next', '')
    if next_page == 'checkout':
        return redirect('checkout')
    return redirect('address_book')

def validate_address_data(form_data):
    full_name = form_data['full_name']
    phone_number = form_data['phone_number']
    address_line1 = form_data['address_line1']
    address_line2 = form_data['address_line2']
    city = form_data['city']
    state = form_data['state']
    country = form_data['country']
    pincode = form_data['pincode']
    address_type = form_data['address_type']

    if not full_name:
        return 'Full name is required'

    if not re.match(r'^[A-Za-z ]+$', full_name):
        return 'Full name can contain only letters'

    if len(full_name) < 3:
        return 'Full name must be at least 3 characters'

    if not phone_number:
        return 'Phone number is required'

    if not re.match(r'^\d{10}$', phone_number):
        return 'Enter a valid 10-digit phone number'

    if not address_line1:
        return 'Address Line 1 is required'

    if not address_line2:
        return 'Address Line 2 is required'

    if not city:
        return 'City is required'

    if not re.match(r'^[A-Za-z ]+$', city):
        return 'City can contain only letters'

    if not state:
        return 'State is required'

    if not re.match(r'^[A-Za-z ]+$', state):
        return 'State can contain only letters'

    if not country:
        return 'Please select a country'

    if not pincode:
        return 'Pincode is required'

    if not re.match(r'^\d{6}$', pincode):
        return 'Enter a valid 6-digit pincode'

    if not address_type:
        return 'Please select an address type'

    return None

def get_address_form_data(request, address=None):
    if request.method == 'POST':
        return {
            'full_name': request.POST.get('full_name', '').strip(),
            'phone_number': request.POST.get('phone_number', '').strip(),
            'address_line1': request.POST.get('address_line1', '').strip(),
            'address_line2': request.POST.get('address_line2', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'state': request.POST.get('state', '').strip(),
            'country': request.POST.get('country', '').strip(),
            'pincode': request.POST.get('pincode', '').strip(),
            'address_type': request.POST.get('address_type', '').strip(),
            'is_default': request.POST.get('is_default'),
        }

    if address:
        return {
            'full_name': address.full_name,
            'phone_number': address.phone_number,
            'address_line1': address.address_line1,
            'address_line2': address.address_line2,
            'city': address.city,
            'state': address.state,
            'country': address.country,
            'pincode': address.pincode,
            'address_type': address.address_type,
            'is_default': address.is_default,
        }

    return {
        'full_name': '',
        'phone_number': '',
        'address_line1': '',
        'address_line2': '',
        'city': '',
        'state': '',
        'country': '',
        'pincode': '',
        'address_type': 'home',
        'is_default': False,
    }


def address_form_context(request, error=None, address=None):
    return {
        'error': error,
        'address': address,
        'next': request.POST.get('next', request.GET.get('next', '')),
        'form_data': get_address_form_data(request, address),
    }

@login_required
@never_cache
def edit_address(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    if request.method == 'POST':
        form_data = get_address_form_data(request, address)
        error = validate_address_data(form_data)

        if error:
            return render(
                request,
                'add_address.html',
                address_form_context(request, error, address)
            )

        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        address.full_name = form_data['full_name']
        address.phone_number = form_data['phone_number']
        address.address_line1 = form_data['address_line1']
        address.address_line2 = form_data['address_line2']
        address.city = form_data['city']
        address.state = form_data['state']
        address.country = form_data['country']
        address.pincode = form_data['pincode']
        address.address_type = form_data['address_type']
        address.is_default = True if request.POST.get('is_default') else False

        address.save()

        messages.success(request, "Address updated successfully!")

        next_page = request.POST.get('next', '')
        if next_page == 'checkout':
            return redirect('checkout')

        return redirect('address_book')

    return render(
        request,
        'add_address.html',
        address_form_context(request, address=address)
    )

@login_required
@never_cache
def edit_profile(request):
    user=request.user
    if request.method=='POST':
        if 'update_profile' in request.POST:
            
            full_name = request.POST.get('full_name', '').strip()
            mobile_number = request.POST.get('mobile_number', '').strip()

            # Full Name
            if not full_name:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Full name is required'
                })

            if not re.match(r'^[A-Za-z ]+$', full_name):
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Full name can contain only letters'
                })

            if len(full_name) < 3:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Full name must be at least 3 characters'
                })

           
            # Mobile Number
            if not mobile_number:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Mobile number is required'
                })

            if not re.match(r'^\d{10}$', mobile_number):
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Enter a valid 10-digit mobile number'
                })

            # Profile Image Validation
            if request.FILES.get('profile_image'):
                image = request.FILES['profile_image']
                user.profile_image = image
            
            user.full_name = full_name
            user.mobile_number = mobile_number

            user.save()
            messages.success(request, "Profile updated successfully!")

        elif 'update_email' in request.POST:            
            email = request.POST.get('email', '').strip()
             # Email
            if not email:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Email is required'
                })

            try:
                validate_email(email)
            except ValidationError:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Enter a valid email address'
                })

            # Email already exists
            if (
                User.objects.filter(email=email)
                .exclude(id=user.id)
                .exists()
            ):
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'error': 'Email already exists'
                })

            otp = str(random.randint(100000, 999999))

            OTP.objects.create(
                email=email,
                otp_code=otp
            )

            send_mail(
                'Scentora Email Change OTP',
                f'Your OTP is {otp}. It will be valid for 2 minutes.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            request.session['otp_purpose'] = 'change_email'
            request.session['new_email'] = email
            request.session['current_user_email'] = email
            return redirect('verify_otp')         

        elif 'change_password' in request.POST:
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not current_password:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'Current password is required'
                })

            password_error = validate_password(new_password, confirm_password)
            if password_error:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': password_error
                })

            # current password check
            if not user.check_password(current_password):
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'Current password is incorrect'
                })

            # same password check
            if current_password == new_password:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'New password cannot be same as old password'
                })

            otp = str(random.randint(100000, 999999))

            OTP.objects.create(
                email=user.email,
                otp_code=otp
            )

            send_mail(
                'Scentora Password Change OTP',
                f'Your OTP is {otp}. It will be valid for 2 minutes.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            request.session['current_user_email'] = user.email
            request.session['otp_purpose'] = 'change_password'
            request.session['new_password'] = new_password
            return redirect('verify_otp')
        
        return redirect('edit_profile')
    return render(request, 'edit_profile.html', {'user': user})

@login_required
@never_cache
def my_orders(request):
    user = request.user

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '').strip()

    orders = Order.objects.filter(user=user).order_by('-created_at')

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(items__product_variant__product__product_name__icontains=search_query)
        ).distinct()

    if status_filter == 'delivered':
        orders = orders.filter(order_status='delivered')
    elif status_filter == 'pending':
        orders = orders.filter(order_status='pending')
    elif status_filter == 'cancelled':
        orders = orders.filter(order_status='cancelled')

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'my_orders.html', context)

@login_required
@never_cache
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product_variant__product').all()

    # for each item, check reviewability + fetch existing review if any
    review_map = {}
    for item in order_items:
        product = item.product_variant.product
        existing = Review.objects.filter(user=request.user, product=product).first()
        review_map[item.id] = {
            'product_id': product.id,
            'variant_id': item.product_variant.id,
            'can_review': order.order_status == 'delivered' and existing is None,
            'existing_review': existing,
        }

    has_active_items = order_items.filter(status='active').exists()

    context = {
        'order': order,
        'order_items': order_items,
        'review_map': review_map,
        'has_active_items': has_active_items,
    }
    return render(request, 'order_detail.html', context)

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product_variant__product').all()

    # create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.pdf"'

    # create PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # title
    title_style = ParagraphStyle('title', fontSize=20, spaceAfter=10, textColor=colors.black, fontName='Helvetica-Bold')
    elements.append(Paragraph("SCENTORA", title_style))
    elements.append(Paragraph("Invoice", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))

    # order info
    elements.append(Paragraph(f"Order Number: {order.order_number}", styles['Normal']))
    elements.append(Paragraph(f"Order Date: {order.created_at.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Paragraph(f"Payment Method: {order.get_payment_method_display()}", styles['Normal']))
    elements.append(Paragraph(f"Order Status: {order.order_status.capitalize()}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # shipping address
    elements.append(Paragraph("Shipping Address", styles['Heading3']))
    elements.append(Paragraph(f"{order.order_address.full_name}", styles['Normal']))
    elements.append(Paragraph(f"{order.order_address.address_line1}", styles['Normal']))
    if order.order_address.address_line2:
        elements.append(Paragraph(f"{order.order_address.address_line2}", styles['Normal']))
    elements.append(Paragraph(f"{order.order_address.city}, {order.order_address.state} - {order.order_address.pincode}", styles['Normal']))
    elements.append(Paragraph(f"{order.order_address.country}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {order.order_address.phone_number}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # order items table
    elements.append(Paragraph("Items Ordered", styles['Heading3']))
    table_data = [['Product', 'Size', 'Qty', 'Unit Price', 'Total']]

    for item in order_items:
        table_data.append([
            item.product_variant.product.product_name,
            f"{item.product_variant.size}ml",
            str(item.quantity),
            f"Rs.{item.price}",
            f"Rs.{item.total}",
        ])

    table = Table(table_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    # totals
    totals_data = [
        ['Subtotal', f"Rs.{order.total_amount}"],
        ['Shipping', 'Free' if order.total_amount == order.final_amount else f"Rs.{order.final_amount - order.total_amount}"],
        ['Discount', f"Rs.{order.discount_amount}"],
        ['Total', f"Rs.{order.final_amount}"],
    ]
    totals_table = Table(totals_data, colWidths=[5*inch, 1.7*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.3 * inch))

    # footer
    elements.append(Paragraph("Thank you for shopping with Scentora!", styles['Normal']))

    doc.build(elements)
    return response

@login_required
@never_cache
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # only allow cancellation if order is pending or processing
    if order.order_status not in ['pending', 'processing']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if len(reason) < 10:
            messages.error(request, "Cancellation reason must be at least 10 characters.")
            return redirect('order_detail', order_id=order.id)

        # increment stock for each item
        for item in order.items.select_related('product_variant').all():
            item.product_variant.stock += item.quantity
            item.product_variant.save()
            item.status = 'cancelled'  # marking each item as cancelled too
            item.save()

        # update order status
        order.order_status = 'cancelled'
        order.cancel_reason = reason
        order.save()

        # Wallet refund for cancellation — direct, no admin approval needed
        if order.payment_status == 'paid' and not has_been_refunded(order):
            credit_wallet(
                user=order.user,
                amount=order.final_amount,
                description=f"Refund for cancelled Order #{order.order_number}",
                order=order,
            )
            messages.success(request, f"Order cancelled. ₹{order.final_amount} refunded to your wallet.")
        else:
            messages.success(request, "Order cancelled successfully.")

        # Also mark payment as failed if it's still pending (Razorpay abandoned orders)
        if hasattr(order, 'payment_detail') and order.payment_detail.payment_status == 'pending':
            order.payment_detail.mark_failed()
            
        messages.success(request, "Order cancelled successfully.")
        return redirect('order_detail', order_id=order.id)

    return redirect('order_detail', order_id=order.id)

@login_required
@never_cache
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    # only allow cancellation if order is pending or processing
    if order.order_status not in ['pending', 'processing']:
        messages.error(request, "Items cannot be cancelled at this stage.")
        return redirect('order_detail', order_id=order.id)

    # only allow if item is still active
    if item.status == 'cancelled':
        messages.error(request, "This item is already cancelled.")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':

        # increment stock back
        item.product_variant.stock += item.quantity
        item.product_variant.save()

        # cancel the item
        item.status = 'cancelled'
        item.save()

        # Refund just this item's amount if order was paid — proportionally split coupon
        if order.payment_status == 'paid':
            refund_amount = calculate_item_refund(item)
            if refund_amount > 0 and not has_item_been_refunded(item):
                credit_wallet(
                    user=order.user,
                    amount=refund_amount,
                    description=f"Refund for cancelled item ({item.product_variant}) in Order #{order.order_number}",
                    order=order,
                    order_item=item,
                )

        # check if all items are cancelled  then cancel entire order
        all_cancelled = not order.items.filter(status='active').exists()
        if all_cancelled:
            order.order_status = 'cancelled'
            order.save()
            messages.success(request, "All items cancelled. Order has been cancelled.")
        else:
            messages.success(request, "Item cancelled successfully.")

        return redirect('order_detail', order_id=order.id)

    return redirect('order_detail', order_id=order.id)

@login_required
@never_cache
def return_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    if order.order_status != 'delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('order_detail', order_id=order.id)

    if item.status != 'active':
        messages.error(request, "This item cannot be returned.")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if len(reason) < 10:
            messages.error(request, "Return reason must be at least 10 characters.")
            return redirect('order_detail', order_id=order.id)

        item.return_reason = reason
        item.status = 'return_requested'
        item.save()

        messages.success(request, "Return request submitted for this item. We'll review it shortly.")
        return redirect('order_detail', order_id=order.id)

    return redirect('order_detail', order_id=order.id)

@login_required
@never_cache
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.order_status != 'delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('order_detail', order_id=order.id)

    active_items = order.items.filter(status='active')

    if not active_items.exists():
        messages.error(request, "There are no items left to return in this order.")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if len(reason) < 10:
            messages.error(request, "Return reason must be at least 10 characters.")
            return redirect('order_detail', order_id=order.id)

        # mark every currently-active item as return_requested,
        # so the admin approval flow (per item, with correct proportional
        # coupon refund) handles each one exactly like an individual return
        active_items.update(status='return_requested', return_reason=reason)

        messages.success(request, "Return request submitted for all items. We will review it shortly.")
        return redirect('order_detail', order_id=order.id)

    return redirect('order_detail', order_id=order.id)

@login_required
@never_cache
def wallet_history(request):
    transactions = WalletTransaction.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'balance': get_wallet_balance(request.user),
    }
    return render(request, 'wallet_history.html', context)