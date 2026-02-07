"""
Admin configuration for the shipments app.
"""
from django.contrib import admin
from .models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Admin interface for Shipment model."""

    list_display = ('id', 'order', 'status', 'tracking_number', 'shipped_at', 'delivered_at')
    list_filter = ('status', 'created_at', 'shipped_at')
    search_fields = ('tracking_number', 'order__id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    actions = ['mark_as_shipped', 'mark_as_delivered']

    def mark_as_shipped(self, request, queryset):
        """Admin action to mark shipments as shipped."""
        for shipment in queryset.filter(status=Shipment.Status.PENDING):
            shipment.mark_as_shipped()
        self.message_user(request, "Selected shipments have been marked as shipped.")
    mark_as_shipped.short_description = "Mark selected shipments as shipped"

    def mark_as_delivered(self, request, queryset):
        """Admin action to mark shipments as delivered."""
        for shipment in queryset.filter(status=Shipment.Status.SHIPPED):
            shipment.mark_as_delivered()
        self.message_user(request, "Selected shipments have been marked as delivered.")
    mark_as_delivered.short_description = "Mark selected shipments as delivered"
