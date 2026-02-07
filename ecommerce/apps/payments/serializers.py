"""
Serializers for the payments app.
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

from apps.orders.models import Order
from .models import Payment, OrderPayment


class OrderPaymentSerializer(serializers.ModelSerializer):
    """Serializer for OrderPayment model."""

    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_total = serializers.DecimalField(
        source='order.total',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderPayment
        fields = ('id', 'order_id', 'order_total', 'amount_applied', 'created_at')
        read_only_fields = ('id', 'created_at')


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    order_payments = OrderPaymentSerializer(many=True, read_only=True)
    amount_applied = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = (
            'id', 'amount', 'method', 'status',
            'amount_applied', 'remaining_amount',
            'order_payments', 'created_at'
        )
        read_only_fields = ('id', 'status', 'created_at')


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments."""

    class Meta:
        model = Payment
        fields = ('id', 'amount', 'method', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class ApplyPaymentSerializer(serializers.Serializer):
    """Serializer for applying a payment to orders."""

    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    amounts = serializers.ListField(
        child=serializers.DecimalField(max_digits=10, decimal_places=2),
        required=False
    )

    def validate(self, attrs):
        order_ids = attrs['order_ids']
        amounts = attrs.get('amounts', [])

        # If amounts provided, must match order count
        if amounts and len(amounts) != len(order_ids):
            raise serializers.ValidationError(
                "Number of amounts must match number of orders."
            )

        # Validate all orders exist and belong to user
        request = self.context.get('request')
        user = request.user if request else None

        orders = Order.objects.filter(id__in=order_ids)
        if orders.count() != len(order_ids):
            raise serializers.ValidationError("One or more orders not found.")

        if user and not user.is_staff:
            for order in orders:
                if order.user != user:
                    raise serializers.ValidationError(
                        f"Order #{order.id} does not belong to you."
                    )

        # Check orders are in pending status
        for order in orders:
            if order.status != Order.Status.PENDING:
                raise serializers.ValidationError(
                    f"Order #{order.id} is not in pending status."
                )

        attrs['orders'] = orders
        return attrs

    @transaction.atomic
    def apply_payment(self, payment):
        """Apply the payment to the specified orders."""
        orders = self.validated_data['orders']
        amounts = self.validated_data.get('amounts', [])

        if not amounts:
            # Distribute payment evenly or by order remaining amount
            remaining = payment.remaining_amount
            for order in orders:
                order_remaining = order.total - order.total_paid
                amount_to_apply = min(remaining, order_remaining)

                if amount_to_apply > 0:
                    OrderPayment.objects.create(
                        order=order,
                        payment=payment,
                        amount_applied=amount_to_apply
                    )
                    remaining -= amount_to_apply

                    # Update order status if fully paid
                    order.refresh_from_db()
                    if order.is_fully_paid:
                        order.status = Order.Status.PAID
                        order.save(update_fields=['status'])
        else:
            # Apply specific amounts
            total_to_apply = sum(amounts)
            if total_to_apply > payment.remaining_amount:
                raise serializers.ValidationError(
                    "Total amounts exceed available payment amount."
                )

            for order, amount in zip(orders, amounts):
                order_remaining = order.total - order.total_paid
                if amount > order_remaining:
                    raise serializers.ValidationError(
                        f"Amount {amount} exceeds remaining balance for order #{order.id}."
                    )

                OrderPayment.objects.create(
                    order=order,
                    payment=payment,
                    amount_applied=amount
                )

                # Update order status if fully paid
                order.refresh_from_db()
                if order.is_fully_paid:
                    order.status = Order.Status.PAID
                    order.save(update_fields=['status'])

        return payment


class PaymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for payment listings."""

    class Meta:
        model = Payment
        fields = ('id', 'amount', 'method', 'status', 'created_at')
