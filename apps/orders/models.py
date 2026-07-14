from django.db import models
from django.utils import timezone
from apps.authentication.models import User
from apps.products.models import ProductVariant

class OrderAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_addresses')
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    address_type = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

class Order(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
    )

    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),    
        ('razorpay', 'Razorpay'),
        ('wallet', 'Wallet'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_address = models.ForeignKey(OrderAddress, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    return_reason = models.TextField(blank=True, null=True)
    cancel_reason = models.TextField(blank=True, null=True)
    coupon = models.ForeignKey('Coupon',on_delete=models.SET_NULL,null=True,blank=True,related_name='orders')
    coupon_discount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number} by {self.user.full_name}"


class OrderItem(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    return_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_variant} in Order #{self.order.order_number}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid',    'Paid'),
        ('failed',  'Failed'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cod',      'Cash on Delivery'),
        ('razorpay', 'Razorpay'),
        ('wallet', 'Wallet'),
        
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment_detail')
    razorpay_order_id   = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method      = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_date    = models.DateTimeField(null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def mark_paid(self, razorpay_payment_id):
        from django.utils import timezone
        self.razorpay_payment_id = razorpay_payment_id
        self.payment_status      = 'paid'
        self.transaction_date    = timezone.now()
        self.save()

    def mark_failed(self):
        self.payment_status = 'failed'
        self.save()

    def __str__(self):
        return f"Payment for Order #{self.order.order_number} — {self.payment_status}"
class Coupon(models.Model):

    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('flat',       'Flat Amount'),
    )
    STATUS_CHOICES = (
        ('active',   'Active'),
        ('inactive', 'Inactive'),
    )

    coupon_code    = models.CharField(max_length=20, unique=True)
    discount_type  = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_price  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_redeem = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date    = models.DateField()
    usage_limit    = models.PositiveIntegerField(default=1)
    used_count     = models.PositiveIntegerField(default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def is_valid(self):
        today = timezone.now().date()
        return (
            self.status == 'active' and
            today <= self.expiry_date and
            self.used_count < self.usage_limit
        )

    def calculate_discount(self, cart_total):
        from decimal import Decimal
        if self.discount_type == 'percentage':
            discount = cart_total * self.discount_value / Decimal('100')
            if self.maximum_redeem:
                discount = min(discount, self.maximum_redeem)
        else:
            discount = self.discount_value
        return min(discount, cart_total)

    def __str__(self):
        return f"{self.coupon_code} — {self.discount_type} — {self.discount_value}"

class CouponUsage(models.Model):
    coupon  = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user    = models.ForeignKey(User,   on_delete=models.CASCADE, related_name='coupon_usages')
    order   = models.ForeignKey(Order,  on_delete=models.CASCADE, related_name='coupon_usage', null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'user')

    def __str__(self):
        return f"{self.user.full_name} used {self.coupon.coupon_code}"