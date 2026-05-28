from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.authentication.models import User, OTP
from .models import Address
import random
from django.core.mail import send_mail
from django.conf import settings


@login_required
def profile_dashboard(request):
    user=request.user

    context = {
        'current_user':user,
        'total_orders': 0,
        'wishlist_count': 0,
        'wallet_balance': 0,
        'pending_orders': 0,
    }
    return render(request,'userprofile.html',context)
    
@login_required   
def address_book(request):
     addresses=Address.objects.filter(user=request.user)

     context={
          'addresses':addresses
     }

     return render(request,'address_book.html',context)

@login_required
def add_address(request):
    if request.method == 'POST':
        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
              user=request.user,
              full_name=request.POST.get('full_name'),
              phone_number=request.POST.get('phone_number'),
              address_line1=request.POST.get('address_line1'),
              address_line2=request.POST.get('address_line2'),
              city=request.POST.get('city'),
              state=request.POST.get('state'),
              country=request.POST.get('country'),
              pincode=request.POST.get('pincode'),
              address_type=request.POST.get('address_type'),
              is_default=True if request.POST.get('is_default') else False
        )
        return redirect('address_book')
    return render(request,'add_address.html')

@login_required
def delete_address(request,address_id):
    address=get_object_or_404(
        Address,
        user=request.user,
        id=address_id
    )

    address.delete()

    return redirect('address_book')

@login_required
def edit_address(request,address_id):
    try:
        address=Address.objects.get(
            id=address_id,
            user=request.user
            )
    except Address.DoesNotExist:
        return redirect('address_book')    
    
    if request.method=='POST':

        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        address.full_name = request.POST.get('full_name')
        address.phone_number = request.POST.get('phone_number')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.pincode = request.POST.get('pincode')
        address.address_type = request.POST.get('address_type')
        address.is_default=True if request.POST.get('is_default') else False

        address.save()
        return redirect('address_book')
    return render(request,'add_address.html', {'address':address})

@login_required
def edit_profile(request):
    user=request.user

    if request.method=='POST':
        if 'update_profile' in request.POST:

            user.full_name=request.POST.get('full_name')
            user.email = request.POST.get('email')
            user.mobile_number = request.POST.get('mobile_number')
            if request.FILES.get('profile_image'):
                user.profile_image = request.FILES['profile_image']

            user.save()

        # PASSWORD CHANGE
        elif 'change_password' in request.POST:
            current_password=request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')   

            # current password check
            if not user.check_password(current_password):
                return render(request,'edit_profile.html',{
                            'error': 'Current password is incorrect'})
            
            # password match
            if new_password != confirm_password:

                return render(request, 'edit_profile.html', {
                    'error': 'Passwords do not match'
                })
            
            # same password check
            if current_password == new_password:

                return render(request, 'edit_profile.html', {
                    'error': 'New password cannot be same as old password'
                })
            
            # generate otp
            otp = str(random.randint(100000, 999999))

            OTP.objects.create(
                email=user.email,
                otp_code=otp
            )
            
            # send mail
            send_mail(
                'Scentora Password Change OTP',
                f'Your OTP is {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            # store session
            request.session['reset_email'] = user.email

            request.session['otp_purpose'] = 'change_password'

            request.session['new_password'] = new_password

            return redirect('verify_otp')

        return redirect('edit_profile')
    return render(request, 'edit_profile.html', {'user': user})