from django.shortcuts import render, redirect
from .models import User,OTP
from django.contrib.auth import authenticate, login
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash

def signup(request):

    if request.method == 'POST':

        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        mobile_number = request.POST.get('mobile_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral = request.POST.get('referral')

        # password match validation
        if password != confirm_password:
            return render(request, 'signup.html', {
                'error': 'Passwords do not match'
            })

        # email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'error': 'Email already exists'
            })
        #mobile number validation
        if User.objects.filter(mobile_number=mobile_number).exists():
            return render(request, 'signup.html', {
                'error': 'Mobile number already exists'
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

        request.session['reset_email'] = email
        request.session['otp_purpose'] = 'signup'

        return redirect('verify_otp')

    return render(request, 'signup.html')


def login_view(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            # blocked user check
            if not user.is_active:
                return render(request, 'login.html', {
                    'error': 'Your account has been blocked'
                })
            login(request, user)

            return redirect('home')

        else:

            return render(request, 'login.html', {
                'error': 'Invalid email or password'
            })

    return render(request, 'login.html')

def forgot_password(request):

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

            request.session['reset_email'] = email
            request.session['otp_purpose'] = 'forgotp'

            return redirect('verify_otp')

        except User.DoesNotExist:

            print('User does not exist')

    return render(
        request,
        'forgot_password.html'
    )

def verify_otp(request):

    if request.method == 'POST':

        entered_otp = (
        request.POST.get('otp1', '') +
        request.POST.get('otp2', '') +
        request.POST.get('otp3', '') +
        request.POST.get('otp4', '') +
        request.POST.get('otp5', '') +
        request.POST.get('otp6', '')
)

        email = request.session.get('reset_email')
        otp_purpose = request.session.get('otp_purpose')

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

                return redirect('login')
            
            elif otp_purpose=='change_password':
                new_password=request.session.get('new_password')
                user = request.user
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user) 
                return redirect('edit_profile')

            return redirect('reset_password')

        except OTP.DoesNotExist:

            return render(request, 'verify_otp.html', {
                'error': 'Invalid OTP'
            })

    return render(request, 'verify_otp.html')

def reset_password(request):

    if request.method == 'POST':

        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:

            return render(request, 'reset_password.html', {
                'error': 'Passwords do not match'
            })

        email = request.session.get('reset_email')

        user = User.objects.get(email=email)

        user.set_password(password)
        user.save()

        return redirect('login')

    return render(request, 'reset_password.html')

def resend_otp(request):

    email = request.session.get('reset_email')

    if not email:
        return redirect('forgot_password')

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