"""
Payment models for the e-commerce application.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Payment(models.Model):
    """Payment model representing a payment transaction."""

    class Method(models.TextChoices):
        CARD = 'card', 'Credit/Debit Card'
        TRANSFER = 'transfer', 'Bank Transfer'
        CASH = 'cash', 'Cash'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment #{self.id} - {self.amount} ({self.status})'

    @property
    def amount_applied(self):
        """Get total amount applied to orders."""
        return sum(op.amount_applied for op in self.order_payments.all())

    @property
    def remaining_amount(self):
        """Get remaining amount that can be applied."""
        return self.amount - self.amount_applied


class OrderPayment(models.Model):
    """Intermediate model linking payments to orders (M:N relationship)."""

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='order_payments'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='order_payments'
    )
    amount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['order', 'payment']
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment #{self.payment.id} -> Order #{self.order.id}: {self.amount_applied}'
