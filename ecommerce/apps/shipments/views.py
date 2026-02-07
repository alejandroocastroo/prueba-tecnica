"""
Views for the shipments app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsAdminOrReadOnly
from .models import Shipment
from .serializers import (
    ShipmentSerializer,
    ShipmentCreateSerializer,
    ShipmentListSerializer,
    ShipmentStatusUpdateSerializer
)
from .tasks import send_shipment_notification


class ShipmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Shipment operations."""

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Shipment.objects.all().select_related('order__user')
        return Shipment.objects.filter(
            order__user=user
        ).select_related('order__user')

    def get_serializer_class(self):
        if self.action == 'create':
            return ShipmentCreateSerializer
        if self.action == 'list':
            return ShipmentListSerializer
        if self.action in ['ship', 'deliver']:
            return ShipmentStatusUpdateSerializer
        return ShipmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'ship', 'deliver', 'destroy']:
            return [IsAuthenticated(), IsAdminOrReadOnly()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark shipment as shipped."""
        shipment = self.get_object()

        if shipment.status != Shipment.Status.PENDING:
            return Response(
                {'error': 'Only pending shipments can be shipped.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment.mark_as_shipped()

        # Send async notification
        send_shipment_notification.delay(shipment.id, 'shipped')

        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Mark shipment as delivered."""
        shipment = self.get_object()

        if shipment.status != Shipment.Status.SHIPPED:
            return Response(
                {'error': 'Only shipped shipments can be delivered.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment.mark_as_delivered()

        # Send async notification
        send_shipment_notification.delay(shipment.id, 'delivered')

        return Response(ShipmentSerializer(shipment).data)

    @action(detail=False, methods=['get'], url_path='by-order/(?P<order_id>[^/.]+)')
    def by_order(self, request, order_id=None):
        """Get shipments for a specific order."""
        shipments = self.get_queryset().filter(order_id=order_id)
        serializer = ShipmentListSerializer(shipments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='track/(?P<tracking_number>[^/.]+)')
    def track(self, request, tracking_number=None):
        """Track shipment by tracking number."""
        try:
            shipment = Shipment.objects.select_related('order__user').get(
                tracking_number=tracking_number
            )

            # Check permission
            user = request.user
            if not user.is_staff and shipment.order.user != user:
                return Response(
                    {'error': 'Shipment not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(ShipmentSerializer(shipment).data)

        except Shipment.DoesNotExist:
            return Response(
                {'error': 'Shipment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
