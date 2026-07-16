import re

def validate_password(password, confirm_password=None):
    if len(password) == 0:
        return "Password is required"
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password) > 128:
        return "Password cannot exceed 128 characters"
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number"
    if not re.search(r'[@$!%*?&]', password):
        return "Password must contain at least one special character"
    if confirm_password is not None:
        if len(confirm_password) == 0:
            return "Confirm password is required"
        if password != confirm_password:
            return "Passwords do not match"
    return None
