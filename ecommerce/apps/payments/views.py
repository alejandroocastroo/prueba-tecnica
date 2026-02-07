"""
Views for the payments app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Payment, OrderPayment
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentListSerializer,
    ApplyPaymentSerializer
)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment operations."""

    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        if self.action == 'list':
            return PaymentListSerializer
        if self.action == 'apply':
            return ApplyPaymentSerializer
        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user

        # For apply action, allow access to any payment (validation happens in serializer)
        if self.action in ['apply', 'retrieve']:
            return Payment.objects.all().prefetch_related('order_payments__order')

        if user.is_staff:
            return Payment.objects.all().prefetch_related('order_payments__order')

        # Get payments for user's orders
        user_order_ids = user.orders.values_list('id', flat=True)
        payment_ids = OrderPayment.objects.filter(
            order_id__in=user_order_ids
        ).values_list('payment_id', flat=True)
        return Payment.objects.filter(id__in=payment_ids).prefetch_related(
            'order_payments__order'
        )

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply payment to specified orders."""
        payment = self.get_object()

        if payment.status != Payment.Status.PENDING:
            return Response(
                {'error': 'Payment is not in pending status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.apply_payment(payment)

        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark payment as completed."""
        payment = self.get_object()

        if payment.status != Payment.Status.PENDING:
            return Response(
                {'error': 'Only pending payments can be completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=['status'])

        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark payment as failed."""
        payment = self.get_object()

        if payment.status != Payment.Status.PENDING:
            return Response(
                {'error': 'Only pending payments can be marked as failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = Payment.Status.FAILED
        payment.save(update_fields=['status'])

        return Response(PaymentSerializer(payment).data)
