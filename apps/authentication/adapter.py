from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        extra = sociallogin.account.extra_data or {}
        email = (extra.get("email") or "").strip().lower()
        if not email:
            return

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        if user.has_usable_password():
            request.session['_social_login_password_restore'] = user.password

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if user.email:
            user.username = user.email

        user.save()
        return user