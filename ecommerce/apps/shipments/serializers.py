"""
Serializers for the shipments app.
"""
from rest_framework import serializers
from .models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer for Shipment model."""

    order_id = serializers.IntegerField(source='order.id', read_only=True)
    user_email = serializers.EmailField(source='order.user.email', read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'id', 'order_id', 'user_email', 'status', 'tracking_number',
            'shipped_at', 'delivered_at', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'tracking_number', 'shipped_at',
            'delivered_at', 'created_at', 'updated_at'
        )


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shipments."""

    order_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Shipment
        fields = ('id', 'order_id', 'status', 'tracking_number', 'created_at')
        read_only_fields = ('id', 'status', 'tracking_number', 'created_at')

    def validate_order_id(self, value):
        from apps.orders.models import Order
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")

        if order.status not in [Order.Status.PAID, Order.Status.SHIPPED]:
            raise serializers.ValidationError(
                "Order must be paid before creating a shipment."
            )

        return value

    def create(self, validated_data):
        from apps.orders.models import Order
        order_id = validated_data.pop('order_id')
        order = Order.objects.get(id=order_id)
        shipment = Shipment.objects.create(order=order, **validated_data)
        return shipment


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating shipment status."""

    status = serializers.ChoiceField(choices=Shipment.Status.choices)

    def validate_status(self, value):
        instance = self.instance
        valid_transitions = {
            Shipment.Status.PENDING: [Shipment.Status.SHIPPED],
            Shipment.Status.SHIPPED: [Shipment.Status.DELIVERED],
            Shipment.Status.DELIVERED: [],
        }

        if value not in valid_transitions.get(instance.status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {instance.status} to {value}."
            )

        return value


class ShipmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for shipment listings."""

    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = Shipment
        fields = ('id', 'order_id', 'status', 'tracking_number', 'created_at')
