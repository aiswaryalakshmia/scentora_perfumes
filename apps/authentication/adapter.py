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
        print("DEBUG pre_social_login email:", email)

        try:
            user = User.objects.get(email__iexact=email)
            # connect Google account to existing user
            sociallogin.connect(request, user)
            print("DEBUG: connected sociallogin to existing user", user.id)
        except User.DoesNotExist:
            print("DEBUG: no existing user for", email)
            pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # ensure username = email
        if user.email:
            user.username = user.email

        # preserve existing password if present
        existing = User.objects.filter(email__iexact=user.email).first()
        if existing and existing.has_usable_password():
            user.password = existing.password

        user.save()
        return user
