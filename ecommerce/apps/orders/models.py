"""
Order models for the e-commerce application.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Order(models.Model):
    """Order model representing a customer's order."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.user.email}'

    def calculate_total(self):
        """Calculate the total from order items."""
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        self.save(update_fields=['total'])
        return total

    @property
    def total_paid(self):
        """Get the total amount paid for this order."""
        return sum(
            op.amount_applied for op in self.order_payments.all()
            if op.payment.status in ('pending', 'completed')
        )

    @property
    def is_fully_paid(self):
        """Check if the order is fully paid."""
        return self.total_paid >= self.total


class OrderItem(models.Model):
    """Order item model representing a product in an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        unique_together = ['order', 'product']

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    @property
    def subtotal(self):
        """Calculate the subtotal for this item."""
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        # Set unit_price from product if not set
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
