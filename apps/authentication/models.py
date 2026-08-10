import random
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def generate_referral_code(length=8):
    chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


class User(AbstractUser):

    full_name = models.CharField(max_length=150)

    email = models.EmailField(unique=True)

    mobile_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )

    status = models.CharField(max_length=10, default="active")

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = generate_referral_code()
            while User.objects.filter(referral_code=code).exists():
                code = generate_referral_code()
            self.referral_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class ReferralUsage(models.Model):
    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals_made"
    )
    referred_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="referred_by"
    )
    referral_code_used = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.full_name} referred {self.referred_user.full_name}"


class OTP(models.Model):

    email = models.EmailField(null=True, blank=True)

    otp_code = models.CharField(max_length=6)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=2)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.email)} - {self.otp_code}"
