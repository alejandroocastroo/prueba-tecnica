"""
Serializers for the orders app.
"""
from rest_framework import serializers
from django.db import transaction

from apps.products.models import Product
from apps.products.serializers import ProductListSerializer
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""

    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_id', 'quantity', 'unit_price', 'subtotal')
        read_only_fields = ('id', 'unit_price', 'subtotal')


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_paid = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'user_email', 'status', 'total',
            'total_paid', 'is_fully_paid', 'items', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'total', 'created_at', 'updated_at')


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""

    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ('id', 'items', 'status', 'total', 'created_at')
        read_only_fields = ('id', 'status', 'total', 'created_at')

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")

        # Check for duplicate products
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products in order.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        # Create order
        order = Order.objects.create(user=user)

        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])

            # Check stock
            if product.stock < item_data['quantity']:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock}"
                )

            # Create item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )

            # Reduce stock
            product.stock -= item_data['quantity']
            product.save(update_fields=['stock'])

        # Calculate total
        order.calculate_total()

        return order


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listings."""

    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'status', 'total', 'items_count', 'created_at')

    def get_items_count(self, obj):
        return obj.items.count()


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status."""

    class Meta:
        model = Order
        fields = ('status',)

    def validate_status(self, value):
        instance = self.instance
        valid_transitions = {
            Order.Status.PENDING: [Order.Status.PAID, Order.Status.CANCELLED],
            Order.Status.PAID: [Order.Status.SHIPPED, Order.Status.CANCELLED],
            Order.Status.SHIPPED: [Order.Status.DELIVERED],
            Order.Status.DELIVERED: [],
            Order.Status.CANCELLED: [],
        }

        if value not in valid_transitions.get(instance.status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {instance.status} to {value}."
            )

        return value
