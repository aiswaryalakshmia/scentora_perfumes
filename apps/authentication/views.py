from django.shortcuts import render, redirect
from .models import User,OTP
from django.contrib.auth import authenticate, login
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

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

        # create user
        user = User.objects.create_user(
            username=email,
            full_name=full_name,
            email=email,
            mobile_number=mobile_number,
            password=password,
            referral_code=referral
        )
        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
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

            user = User.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            OTP.objects.create(
                user=user,
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

            user = User.objects.get(email=email)

            otp_obj = OTP.objects.filter(
                user=user,
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
                return redirect('login')
            
            elif otp_purpose=='change_password':
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

        user = User.objects.get(email=email)

        OTP.objects.filter(
            user=user,
            is_used=False
        ).update(is_used=True)

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
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