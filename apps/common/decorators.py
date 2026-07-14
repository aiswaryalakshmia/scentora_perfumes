from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            # messages.error(request, "Please log in as admin to continue.")
            return redirect('admin_login')

        if not request.user.is_superuser:
            # messages.error(request, "You do not have permission to access the admin panel.")
            return redirect('admin_login')

        return view_func(request, *args, **kwargs)

    return wrapper