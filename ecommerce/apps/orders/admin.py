"""
Admin configuration for the orders app.
"""
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem."""
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""

    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id')
    ordering = ('-created_at',)
    readonly_fields = ('total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""

    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')
