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

        # Stash the existing password hash in the session so it can be
        # restored after the ENTIRE login pipeline finishes, regardless
        # of whether allauth resets it somewhere in between.
        if user.has_usable_password():
            request.session['_social_login_password_restore'] = user.password

        sociallogin.connect(request, user)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if user.email:
            user.username = user.email

        user.save()
        return user