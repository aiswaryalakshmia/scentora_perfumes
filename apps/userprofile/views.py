from django.shortcuts import render,redirect
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from apps.authentication.models import User, OTP
from .models import Address
import random
from django.core.mail import send_mail
from django.conf import settings
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


@login_required
@never_cache
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
@never_cache   
def address_book(request):
     addresses=Address.objects.filter(user=request.user)

     context={
          'addresses':addresses
     }

     return render(request,'address_book.html',context)

@login_required
@never_cache
def add_address(request):
    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        address_type = request.POST.get('address_type', '').strip()

        # FULL NAME
        if not full_name:
            return render(request, 'add_address.html', {
                'error': 'Full name is required'
            })

        if not re.match(r'^[A-Za-z ]+$', full_name):
            return render(request, 'add_address.html', {
                'error': 'Full name can contain only letters'
            })

        if len(full_name) < 3:
            return render(request, 'add_address.html', {
                'error': 'Full name must be at least 3 characters'
            })

        # PHONE NUMBER
        if not phone_number:
            return render(request, 'add_address.html', {
                'error': 'Phone number is required'
            })

        if not re.match(r'^\d{10}$', phone_number):
            return render(request, 'add_address.html', {
                'error': 'Enter a valid 10-digit phone number'
            })

        # ADDRESS LINE 1
        if not address_line1:
            return render(request, 'add_address.html', {
                'error': 'Address Line 1 is required'
            })

        # CITY
        if not city:
            return render(request, 'add_address.html', {
                'error': 'City is required'
            })

        if not re.match(r'^[A-Za-z ]+$', city):
            return render(request, 'add_address.html', {
                'error': 'City can contain only letters'
            })

        # STATE
        if not state:
            return render(request, 'add_address.html', {
                'error': 'State is required'
            })

        if not re.match(r'^[A-Za-z ]+$', state):
            return render(request, 'add_address.html', {
                'error': 'State can contain only letters'
            })

        # COUNTRY
        if not country:
            return render(request, 'add_address.html', {
                'error': 'Please select a country'
            })

        # PINCODE
        if not pincode:
            return render(request, 'add_address.html', {
                'error': 'Pincode is required'
            })

        if not re.match(r'^\d{6}$', pincode):
            return render(request, 'add_address.html', {
                'error': 'Enter a valid 6-digit pincode'
            })

        # ADDRESS TYPE
        if not address_type:
            return render(request, 'add_address.html', {
                'error': 'Please select an address type'
            })

        # DEFAULT ADDRESS
        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone_number,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
            address_type=address_type,
            is_default=True if request.POST.get('is_default') else False
        )

        return redirect('address_book')

    return render(request, 'add_address.html')

@login_required
@never_cache
def delete_address(request,address_id):
    address=get_object_or_404(
        Address,
        user=request.user,
        id=address_id
    )

    address.delete()

    return redirect('address_book')

@login_required
@never_cache
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
@never_cache
def edit_profile(request):
    user=request.user

    if request.method=='POST':
        if 'update_profile' in request.POST:

            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
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

                allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']

                extension = image.name.split('.')[-1].lower()

                if extension not in allowed_extensions:
                    return render(request, 'edit_profile.html', {
                        'user': user,
                        'error': 'Only JPG, JPEG, PNG and WEBP images are allowed'
                    })

                if image.size > 5 * 1024 * 1024:
                    return render(request, 'edit_profile.html', {
                        'user': user,
                        'error': 'Image size must be less than 5 MB'
                    })

                user.profile_image = image

            user.full_name = full_name
            user.email = email
            user.mobile_number = mobile_number

            user.save()

        # PASSWORD CHANGE
        elif 'change_password' in request.POST:
            current_password=request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')   

            if not current_password:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'Current password is required'
                })

            if not new_password:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'New password is required'
                })

            if not confirm_password:
                return render(request, 'edit_profile.html', {
                    'user': user,
                    'password_error': 'Confirm password is required'
                })
            
            if len(new_password)==0:
                return render(request,'edit_profile.html', {
                    'password_error':'Password is required'
                })
            
            # PASSWORD LENGTH
            if len(new_password) < 8:
                return render(request, 'edit_profile.html', {
                    'password_error': 'Password must be at least 8 characters'
                })

            # PASSWORD UPPERCASE
            if not re.search(r'[A-Z]', new_password):
                return render(request, 'edit_profile.html', {
                    'password_error': 'Password must contain at least one uppercase letter'
                })

            # PASSWORD LOWERCASE
            if not re.search(r'[a-z]', new_password):
                return render(request, 'edit_profile.html', {
                    'password_error': 'Password must contain at least one lowercase letter'
                })

            # PASSWORD NUMBER
            if not re.search(r'[0-9]', new_password):
                return render(request, 'edit_profile.html', {
                    'password_error': 'Password must contain at least one number'
                })

            # PASSWORD SPECIAL CHARACTER
            if not re.search(r'[@$!%*?&]', new_password):
                return render(request, 'edit_profile.html', {
                    'password_error': 'Password must contain at least one special character'
                })

            # current password check
            if not user.check_password(current_password):
                return render(request,'edit_profile.html',{
                            'password_error': 'Current password is incorrect'})
            
            # password match
            if new_password != confirm_password:

                return render(request, 'edit_profile.html', {
                    'password_error': 'Passwords do not match'
                })
            
            # same password check
            if current_password == new_password:

                return render(request, 'edit_profile.html', {
                    'password_error': 'New password cannot be same as old password'
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
            request.session['current_user_email'] = user.email

            request.session['otp_purpose'] = 'change_password'

            request.session['new_password'] = new_password

            return redirect('verify_otp')

        return redirect('edit_profile')
    return render(request, 'edit_profile.html', {'user': user})