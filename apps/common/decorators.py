from django.shortcuts import redirect


def admin_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("admin_login")

        if not request.user.is_superuser:
            return redirect("admin_login")

        return view_func(request, *args, **kwargs)

    return wrapper
