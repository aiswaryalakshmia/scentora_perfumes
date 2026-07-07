from decimal import Decimal
from django.db import transaction as db_transaction, models as db_models
from .models import WalletTransaction


def get_wallet_balance(user):
    result = WalletTransaction.objects.filter(user=user).aggregate(
        balance=db_models.Sum(
            db_models.Case(
                db_models.When(transaction_type='credit', then='amount'),
                db_models.When(transaction_type='debit', then=-1 * db_models.F('amount')),
                output_field=db_models.DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )
    return result['balance'] or Decimal('0.00')


def credit_wallet(user, amount, description, order=None):
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Credit amount must be positive.")
    return WalletTransaction.objects.create(
        user=user, order=order, amount=amount,
        transaction_type='credit', description=description,
    )


def debit_wallet(user, amount, description, order=None):
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Debit amount must be positive.")
    with db_transaction.atomic():
        if get_wallet_balance(user) < amount:
            raise ValueError("Insufficient wallet balance.")
        return WalletTransaction.objects.create(
            user=user, order=order, amount=amount,
            transaction_type='debit', description=description,
        )


def has_been_refunded(order):
    # prevents double-crediting the same order on repeated clicks
    return WalletTransaction.objects.filter(
        order=order, transaction_type='credit'
    ).exists()