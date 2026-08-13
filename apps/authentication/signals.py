from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def restore_password_after_social_login(sender, request, user, **kwargs):
    """
    If a user logged in via a social provider (Google) and previously had
    a usable password, allauth's internal pipeline can sometimes wipe it.
    This restores the original hash after the full login process completes,
    which is the last point in the pipeline nothing else can override.
    """
    stored_hash = request.session.pop('_social_login_password_restore', None)
    if stored_hash and not user.has_usable_password():
        user.password = stored_hash
        user.save(update_fields=['password'])