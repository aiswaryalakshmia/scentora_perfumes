"""
Authentication views for user registration, login, logout, OTP verification,
password reset, password change, and session management.
"""
import random
import re
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
from django.contrib import messages
from .models import User,OTP
from .referral_utils import apply_referral_code
from .validators import validate_password

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    referral_prefill = request.GET.get('ref', '').strip().upper()

    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        full_name = " ".join(full_name.split())
        email = request.POST.get('email', '').strip().lower()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        referral = request.POST.get('referral', '').strip().upper()
        base_context = {'referral_prefill': referral_prefill}

        #full name empty check
        if len(full_name)==0:
            return render(request,'signup.html', {**base_context,
                'error':'Full name is required'
            },status=400)

        #letters and spaces only check
        if not re.match(r'^[A-Za-z ]+$', full_name):
            return render(request, 'signup.html', {**base_context,
                'error': 'Full name can contain only letters'
            },status=400)

        #minimum length check
        if len(full_name) < 3:
            return render(request, 'signup.html', {**base_context,
                'error': 'Full name must contain at least 3 characters'
            },status=400)

        #maximum length check
        if len(full_name) > 150:
            return render(request, 'signup.html', {**base_context,
                'error': 'Full name cannot exceed 150 characters'
            },status=400)


        #email empty check
        if len(email)==0:
            return render(request,'signup.html', {**base_context,
                'error':'Email is required'
            },status=400)

        #email maximum length check
        if len(email) > 254:
            return render(request, 'signup.html', {**base_context,
                'error': 'Email address is too long'
            },status=400)

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        #regex validation
        if not re.match(email_pattern, email):
            return render(request, 'signup.html', {**base_context,
                'error': 'Enter a valid email address'
            },status=400)

        #Duplicate email check
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {**base_context,
                'error': 'Email already exists'
            },status=400)

        #mobile number empty check
        if len(mobile_number)==0:
            return render(request,'signup.html', {**base_context,
                'error':'Mobile number is required'
            },status=400)

        #digits only check
        if not mobile_number.isdigit():
            return render(request, 'signup.html', {**base_context,
                'error': 'Mobile number must contain only digits'
            },status=400)

        #mobile number length check
        if len(mobile_number) != 10:
            return render(request, 'signup.html', {**base_context,
                'error': 'Mobile number must be 10 digits'
            },status=400)

        #Duplicate mobile number check
        if User.objects.filter(mobile_number=mobile_number).exists():
            return render(request, 'signup.html', {**base_context,
                'error': 'Mobile number already exists'
            },status=400)
        
        #mobile number starting digit check
        if mobile_number[0] not in '6789':
            return render(request, 'signup.html', {**base_context,
                'error': 'Enter a valid mobile number'
            },status=400)
        
        #password validation
        password_error = validate_password(password, confirm_password)
        if password_error:
            return render(request, 'signup.html', {**base_context, 'error': password_error},status=400)
        
        #referral code length check
        if referral and len(referral) > 20:
            return render(request, 'signup.html', {**base_context,
                'error': 'Referral code is invalid'
            },status=400)

        request.session['signup_data'] = {
            'full_name': full_name,
            'email': email,
            'mobile_number': mobile_number,
            'password': password,
            'referral': referral
        }

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            email=email,
            otp_code=otp
        )

        send_mail(
            'Scentora — Verify Your Email',
            f'Welcome to Scentora!\n\n'
            f'Your verification code is: {otp}\n\n'
            f'This code will expire in 2 minutes. Please enter it to complete your signup.\n\n'
            f'If you did not create an account with Scentora, you can safely ignore this email.\n\n'
            f'— The Scentora Team',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        request.session['current_user_email'] = email
        request.session['otp_purpose'] = 'signup'

        return redirect('verify_otp')

    return render(request, 'signup.html', {
        'referral_prefill': referral_prefill,
    })

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email:
            return render(request, 'login.html', {
                'error': 'Email is required'
            },status=400)

        if not password:
            return render(request, 'login.html', {
                'error': 'Password is required'
            },status=400)

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)
            messages.success(
                request,
                f'Welcome back, {user.full_name}!'
            )
            return redirect('home')

        # blocked user check
        elif User.objects.filter(username=email, is_active=False).exists():
            return render(request, 'login.html', {
                'blocked_error': 'Your account has been blocked. Please contact support.'
            })

        else:
            return render(request, 'login.html', {
                'error': 'Invalid email or password'
            })

    return render(request, 'login.html')

@never_cache
def forgot_password(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()

        if not email:
            return render(request, 'forgot_password.html', {
                'error': 'Email is required'
            },status=400)

        if not User.objects.filter(email=email).exists():
            return render(request, 'forgot_password.html', {
                'error': 'No account found with this email address'
            },status=400)

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            email=email,
            otp_code=otp
        )

        send_mail(
            'Scentora — Password Reset Code',
            f'We received a request to reset your Scentora account password.\n\n'
            f'Your verification code is: {otp}\n\n'
            f'This code will expire in 2 minutes.\n\n'
            f'If you did not request a password reset, please ignore this email — your password will remain unchanged.\n\n'
            f'— The Scentora Team',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        request.session['current_user_email'] = email
        request.session['otp_purpose'] = 'forgotp'

        return redirect('verify_otp')

    return render(request, 'forgot_password.html')

@never_cache
def verify_otp(request):
    email = request.session.get('current_user_email')
    otp_purpose = request.session.get('otp_purpose')

    if not otp_purpose:
        return redirect('login')

    if request.method == 'POST':

        entered_otp = ''.join(request.POST.get(f'otp{i}', '') for i in range(1, 7))

        try:

            otp_obj = OTP.objects.filter(
                email=email,
                otp_code=entered_otp,
                is_used=False
            ).latest('created_at')

            # check expiry
            if timezone.now() > otp_obj.expires_at:
                latest_otp = OTP.objects.filter(email=email, is_used=False).order_by('-created_at').first()
                expires_at_timestamp = None
                if latest_otp:
                    expires_at_timestamp = int(latest_otp.expires_at.timestamp() * 1000)
                return render(request, 'verify_otp.html', {
                    'error': 'OTP expired',
                    'expires_at_timestamp': expires_at_timestamp,
                },status=400)

            # mark OTP used
            otp_obj.is_used = True
            otp_obj.save()

            if otp_purpose=='signup':

                user_details=request.session.get('signup_data')                
                user = User.objects.create_user(
                    username=user_details['email'],
                    full_name=user_details['full_name'],
                    email=user_details['email'],
                    mobile_number=user_details['mobile_number'],
                    password=user_details['password'],
                )
                user.is_verified = True
                user.save()

                # apply referral code entered by this new user
                referral_input = user_details.get('referral', '')
                if referral_input:
                    ref_success, ref_message = apply_referral_code(user, referral_input)
                    if ref_success:
                        messages.success(request, ref_message)

                request.session.pop('signup_data', None)
                request.session.pop('current_user_email', None)
                request.session.pop('otp_purpose', None)

                messages.success(
                    request,
                    'Account created successfully! Please sign in.'
                )

                return redirect('login')

            elif otp_purpose=='change_password':
                new_password=request.session.get('new_password')
                user = request.user
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user) 
                messages.success(
                    request,
                'Password changed successfully!'
    )
                request.session.pop('otp_purpose', None)
                request.session.pop('new_password', None)
                return redirect('edit_profile')
            
            elif otp_purpose=='change_email':
                new_email=request.session.get('new_email')
                user = request.user
                user.email = new_email
                user.save()
                messages.success(request, "Email updated successfully!")

                request.session.pop('otp_purpose', None)
                request.session.pop('new_email', None)
                return redirect('edit_profile')

            elif otp_purpose=='forgotp':
                request.session.pop('otp_purpose', None)                
                
                return redirect('reset_password')

        except OTP.DoesNotExist:
            latest_otp = OTP.objects.filter(email=email, is_used=False).order_by('-created_at').first()
            expires_at_timestamp = None
            if latest_otp:
                expires_at_timestamp = int(latest_otp.expires_at.timestamp() * 1000)
            return render(request, 'verify_otp.html', {
                'error': 'Invalid OTP',
                'expires_at_timestamp': expires_at_timestamp,
            },status=400)

    latest_otp = OTP.objects.filter(email=email, is_used=False).order_by('-created_at').first()
    expires_at_timestamp = None
    if latest_otp:
        expires_at_timestamp = int(latest_otp.expires_at.timestamp() * 1000)  # JS uses milliseconds

    return render(request, 'verify_otp.html', {
        'expires_at_timestamp': expires_at_timestamp,
    })

@never_cache
def reset_password(request):

    email = request.session.get('current_user_email')

    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect('forgot_password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('forgot_password')

    if request.method == 'POST':

        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        password_error = validate_password(password, confirm_password)
        if password_error:
            return render(request, 'reset_password.html', {
                'error': password_error
            },status=400)

        user.set_password(password)
        user.save()

        # clear session AFTER success
        request.session.pop('current_user_email', None)

        messages.success(request, "Password reset successful. Please login.")
        return redirect('login')

    return render(request, 'reset_password.html')

@never_cache
def resend_otp(request):

    email = request.session.get('current_user_email')
    otp_purpose = request.session.get('otp_purpose')

    if not email and otp_purpose=='forgotp':
        return redirect('forgot_password')

    elif not email and otp_purpose=='signup':
        return redirect('signup.html')

    elif not email and otp_purpose=='change_password':
        return redirect('edit_profile.html')

    try:

        OTP.objects.filter(
            email=email,
            is_used=False
        ).update(is_used=True)

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            email=email,
            otp_code=otp
        )

        purpose_text = {
            'signup': 'complete your signup',
            'forgotp': 'reset your password',
            'change_password': 'confirm your password change',
            'change_email': 'confirm your new email address',
        }.get(otp_purpose, 'verify your identity')

        send_mail(
            'Scentora — Your Verification Code',
            f'Here is your new verification code to {purpose_text}:\n\n'
            f'{otp}\n\n'
            f'This code will expire in 2 minutes.\n\n'
            f'If you did not request this, please ignore this email.\n\n'
            f'— The Scentora Team',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return redirect('verify_otp')

    except User.DoesNotExist:

        return redirect('forgot_password')

@never_cache   
def logout_view(request):
    logout(request)
    return redirect('login')
