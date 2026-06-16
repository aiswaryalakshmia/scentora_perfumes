from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        extra = sociallogin.account.extra_data or {}
        email = extra.get("email")
        if not email:
            return

        email = email.strip().lower()

        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        email = sociallogin.account.extra_data.get("email", "").strip().lower()
        
        original_password = None
        if email:
            existing = User.objects.filter(email__iexact=email).first()
            if existing and existing.has_usable_password():
                original_password = existing.password  # Save it now
        
        user = super().save_user(request, sociallogin, form)
       
        if original_password:
            user.password = original_password
        
        if user.email:
            user.username = user.email

        user.save()
        return user