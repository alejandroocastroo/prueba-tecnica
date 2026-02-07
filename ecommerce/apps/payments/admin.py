"""
Admin configuration for the payments app.
"""
from django.contrib import admin
from .models import Payment, OrderPayment


class OrderPaymentInline(admin.TabularInline):
    """Inline admin for OrderPayment."""
    model = OrderPayment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""

    list_display = ('id', 'amount', 'method', 'status', 'created_at')
    list_filter = ('status', 'method', 'created_at')
    search_fields = ('id',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    inlines = [OrderPaymentInline]


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    """Admin interface for OrderPayment model."""

    list_display = ('id', 'order', 'payment', 'amount_applied', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__id', 'payment__id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
