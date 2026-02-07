"""
Views for the orders app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsOwnerOrAdmin
from .models import Order
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order operations."""

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('items__product')
        return Order.objects.filter(user=user).prefetch_related('items__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'list':
            return OrderListSerializer
        if self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'update_status']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update order status with validation."""
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=['get'], url_path='my-orders')
    def my_orders(self, request):
        """Get current user's orders."""
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
