from django.db import models
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number} by {self.user.full_name}"


class OrderItem(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

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
    )

    order               = models.OneToOneField(
                              Order,
                              on_delete=models.CASCADE,
                              related_name='payment_detail'
                          )
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