"""
Serializers for the products app.
"""
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'stock',
            'is_active', 'is_in_stock', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings."""

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'is_active')
