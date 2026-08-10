from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from apps.products.models import Category, ProductVariant
from apps.products.utils import get_offer_price


@never_cache
def home(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    categories = Category.objects.filter(status="active")

    new_arrivals = (
        ProductVariant.objects.filter(
            status="active",
            product__status="active",
            product__category__status="active",
            stock__gt=0,
        )
        .select_related("product", "product__category")
        .prefetch_related("images")
        .order_by("-created_at")[:4]
    )

    for v in new_arrivals:
        fp, _, _ = get_offer_price(v)
        v.final_price = fp

    return render(
        request,
        "home.html",
        {
            "categories": categories,
            "new_arrivals": new_arrivals,
        },
    )


def about(request):
    return render(request, "user/about.html")


def contact_us(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "General Inquiry")
        message = request.POST.get("message", "").strip()

        if not full_name:
            messages.error(request, "Full name is required.")
            return redirect("contact_us")

        if not email:
            messages.error(request, "Email address is required.")
            return redirect("contact_us")

        if not message:
            messages.error(request, "Please enter a message.")
            return redirect("contact_us")

        send_mail(
            f"Scentora Contact Form: {subject}",
            f"From: {full_name} <{email}>\n\nSubject: {subject}\n\nMessage:\n{message}",
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        messages.success(
            request, "Your message has been sent! We'll get back to you soon."
        )
        return redirect("contact_us")

    return render(request, "user/contact_us.html")
