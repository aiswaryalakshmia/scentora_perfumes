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
        except User.DoesNotExist:
            return

        original_password = user.password  # capture the real hash before connect() can wipe it

        sociallogin.connect(request, user)

        # connect() may call set_unusable_password() + save() internally on `user`.
        # Restore the original password hash so email/password login keeps working.
        user.refresh_from_db()
        if not user.has_usable_password() and original_password:
            user.password = original_password
            user.save(update_fields=['password'])

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if user.email:
            user.username = user.email

        user.save()
        return user