from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):

    full_name = models.CharField(max_length=150)

    email = models.EmailField(unique=True)

    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True
    )

    referral_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )


    status = models.CharField(
        max_length=10,
        default='active'
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
class OTP(models.Model):

    
    email = models.EmailField(null=True, blank=True)

    otp_code = models.CharField(
        max_length=6
    )

    is_used = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=2)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.user)} - {self.otp_code}"