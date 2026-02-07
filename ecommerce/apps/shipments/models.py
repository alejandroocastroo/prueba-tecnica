"""
Shipment models for the e-commerce application.
"""
import uuid
from django.db import models
from django.utils import timezone


class Shipment(models.Model):
    """Shipment model representing order delivery."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='shipments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Shipment #{self.id} for Order #{self.order_id}'

    def generate_tracking_number(self):
        """Generate a unique tracking number."""
        self.tracking_number = f'TRK-{uuid.uuid4().hex[:12].upper()}'
        return self.tracking_number

    def mark_as_shipped(self):
        """Mark shipment as shipped."""
        if not self.tracking_number:
            self.generate_tracking_number()
        self.status = self.Status.SHIPPED
        self.shipped_at = timezone.now()
        self.save()

        # Update order status
        self.order.status = 'shipped'
        self.order.save(update_fields=['status'])

    def mark_as_delivered(self):
        """Mark shipment as delivered."""
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save()

        # Update order status
        self.order.status = 'delivered'
        self.order.save(update_fields=['status'])
