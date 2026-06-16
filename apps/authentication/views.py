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

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        mobile_number = request.POST.get('mobile_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral = request.POST.get('referral')

        #full name empty check
        if len(full_name)==0:
            return render(request,'signup.html', {
                'error':'Full name is required'
            })

        #minimum length check
        if len(full_name) < 3:
            return render(request, 'signup.html', {
                'error': 'Full name must contain at least 3 characters'
            })

        #email empty check
        if len(email)==0:
            return render(request,'signup.html', {
                'error':'Email is required'
            })

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        #regex validation
        if not re.match(email_pattern, email):
            return render(request, 'signup.html', {
                'error': 'Enter a valid email address'
            })

        #Duplicate email check
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'error': 'Email already exists'
            })

        #mobile number empty check
        if len(mobile_number)==0:
            return render(request,'signup.html', {
                'error':'Mobile number is required'
            })

        #digits only check
        if not mobile_number.isdigit():
            return render(request, 'signup.html', {
                'error': 'Mobile number must contain only digits'
            })

        #mobile number length check
        if len(mobile_number) != 10:
            return render(request, 'signup.html', {
                'error': 'Mobile number must be 10 digits'
            })

        #Duplicate mobile number check
        if User.objects.filter(mobile_number=mobile_number).exists():
            return render(request, 'signup.html', {
                'error': 'Mobile number already exists'
            })

        #password empty check
        if len(password)==0:
            return render(request,'signup.html', {
                'error':'Password is required'
            })

        #password length check
        if len(password) < 8:
            return render(request, 'signup.html', {
                'error': 'Password must be at least 8 characters'
            })

        #uppercase check
        if not re.search(r'[A-Z]', password):
            return render(request, 'signup.html', {
                'error': 'Password must contain at least one uppercase letter'
            })

        #lowercase check
        if not re.search(r'[a-z]', password):
            return render(request, 'signup.html', {
                'error': 'Password must contain at least one lowercase letter'
            })

        #number check
        if not re.search(r'[0-9]', password):
            return render(request, 'signup.html', {
                'error': 'Password must contain at least one number'
            })

        #special character check
        if not re.search(r'[@$!%*?&]', password):
            return render(request, 'signup.html', {
                'error': 'Password must contain at least one special character'
            })

        #confirm password empty check
        if len(confirm_password)==0:
            return render(request,'signup.html', {
                'error':'Password is required'
            })

        #password match check
        if password != confirm_password:
            return render(request, 'signup.html', {
                'error': 'Passwords do not match'
            })

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
            'Scentora Signup Verification',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        request.session['current_user_email'] = email
        request.session['otp_purpose'] = 'signup'

        return redirect('verify_otp')

    return render(request, 'signup.html')

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
            })

        if not password:
            return render(request, 'login.html', {
                'error': 'Password is required'
            })

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

        email = request.POST.get('email')

        try:

            otp = str(random.randint(100000, 999999))

            OTP.objects.create(
                email=email,
                otp_code=otp
            )

            send_mail(
                'Scentora Password Reset OTP',
                f'Your OTP is {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            request.session['current_user_email'] = email
            request.session['otp_purpose'] = 'forgotp'

            return redirect('verify_otp')

        except User.DoesNotExist:

            print('User does not exist')

    return render(
        request,
        'forgot_password.html'
    )

@never_cache
def verify_otp(request):
    email = request.session.get('current_user_email')
    otp_purpose = request.session.get('otp_purpose')

    if not otp_purpose:
        return redirect('login')

    if request.method == 'POST':

        entered_otp = (
            request.POST.get('otp1', '') +
            request.POST.get('otp2', '') +
            request.POST.get('otp3', '') +
            request.POST.get('otp4', '') +
            request.POST.get('otp5', '') +
            request.POST.get('otp6', '')
        )

        try:

            otp_obj = OTP.objects.filter(
                email=email,
                otp_code=entered_otp,
                is_used=False
            ).latest('created_at')

            # check expiry
            if timezone.now() > otp_obj.expires_at:

                return render(request, 'verify_otp.html', {
                    'error': 'OTP expired'
                })

            # mark OTP used
            otp_obj.is_used = True
            otp_obj.save()

            if otp_purpose=='signup':

                user_details=request.session.get('signup_data')
                #create user
                user = User.objects.create_user(
                    username=user_details['email'],
                    full_name=user_details['full_name'],
                    email=user_details['email'],
                    mobile_number=user_details['mobile_number'],
                    password=user_details['password'],
                    referral_code=user_details['referral']
                )

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
                new_fullname=request.session.get('new_fullname')
                new_mobile_number=request.session.get('new_mobile_number')
                user = request.user
                user.full_name = new_fullname
                user.email = new_email
                user.mobile_number = new_mobile_number

                user.save()
                messages.success(request, "Profile updated successfully!")

                request.session.pop('otp_purpose', None)
                request.session.pop('new_email', None)
                request.session.pop('new_fullname', None)
                request.session.pop('new_mobile_number', None)
                return redirect('edit_profile')

            elif otp_purpose=='forgotp':
                request.session.pop('otp_purpose', None)                
                
                return redirect('reset_password')

        except OTP.DoesNotExist:
            return render(request, 'verify_otp.html', {
                'error': 'Invalid OTP'
            })

    return render(request, 'verify_otp.html')

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

        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'reset_password.html', {
                'error': 'Passwords do not match'
            })

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

        send_mail(
            'Scentora OTP Verification',
            f'Your new OTP is {otp}',
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
