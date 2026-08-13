from django.contrib.auth.signals import user_logged_in
from django.contrib.auth import update_session_auth_hash
from django.dispatch import receiver


@receiver(user_logged_in)
def restore_password_after_social_login(sender, request, user, **kwargs):
    stored_hash = request.session.pop('_social_login_password_restore', None)
    if stored_hash and not user.has_usable_password():
        user.password = stored_hash
        user.save(update_fields=['password'])
        update_session_auth_hash(request, user)
