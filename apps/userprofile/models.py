from django.db import models
from apps.authentication.models import User
from decimal import Decimal
class Address(models.Model):

    ADDRESS_TYPES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    full_name = models.CharField(max_length=150)

    phone_number = models.CharField(max_length=15)

    address_line1 = models.CharField(max_length=255)

    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    country = models.CharField(max_length=100)

    pincode = models.CharField(max_length=10)

    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPES,
        default='home'
    )

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"   


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('credit', 'Credit'),   # refunds
        ('debit',  'Debit'),    # payments
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} — {self.get_transaction_type_display()} ₹{self.amount}"