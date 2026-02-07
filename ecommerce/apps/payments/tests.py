"""
Tests for the payments app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from .models import Payment, OrderPayment


@pytest.fixture
def product(db):
    """Create a test product."""
    return Product.objects.create(
        name='Test Product',
        price=Decimal('100.00'),
        stock=10,
        is_active=True
    )


@pytest.fixture
def order(db, user, product):
    """Create a test order."""
    order = Order.objects.create(user=user)
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=product.price
    )
    order.calculate_total()
    return order


@pytest.fixture
def payment(db):
    """Create a test payment."""
    return Payment.objects.create(
        amount=Decimal('200.00'),
        method=Payment.Method.CARD,
        status=Payment.Status.PENDING
    )


@pytest.mark.django_db
class TestPaymentCreation:
    """Tests for payment creation."""

    def test_create_payment_success(self, authenticated_client):
        """Test successful payment creation."""
        url = reverse('payments:payment-list')
        data = {
            'amount': '150.00',
            'method': 'card'
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert Decimal(response.data['amount']) == Decimal('150.00')

    def test_create_payment_invalid_amount(self, authenticated_client):
        """Test payment creation with invalid amount."""
        url = reverse('payments:payment-list')
        data = {
            'amount': '-50.00',
            'method': 'card'
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentApply:
    """Tests for applying payments to orders."""

    def test_apply_payment_to_order(self, authenticated_client, order, payment):
        """Test applying payment to an order."""
        url = reverse('payments:payment-apply', args=[payment.id])
        data = {
            'order_ids': [order.id]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        assert order.total_paid == Decimal('200.00')

    def test_apply_payment_specific_amount(self, authenticated_client, order, payment):
        """Test applying specific amount to order."""
        url = reverse('payments:payment-apply', args=[payment.id])
        data = {
            'order_ids': [order.id],
            'amounts': ['100.00']
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        order.refresh_from_db()
        assert order.status == Order.Status.PENDING  # Only half paid
        assert order.total_paid == Decimal('100.00')

    def test_apply_payment_exceeds_remaining(self, authenticated_client, order, payment):
        """Test applying more than remaining amount fails."""
        url = reverse('payments:payment-apply', args=[payment.id])
        data = {
            'order_ids': [order.id],
            'amounts': ['500.00']  # More than order total and payment amount
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_payment_to_non_pending_order(self, authenticated_client, order, payment):
        """Test applying payment to non-pending order fails."""
        order.status = Order.Status.CANCELLED
        order.save()

        url = reverse('payments:payment-apply', args=[payment.id])
        data = {
            'order_ids': [order.id]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentStatus:
    """Tests for payment status changes."""

    def test_complete_payment(self, admin_client, payment):
        """Test marking payment as completed."""
        url = reverse('payments:payment-complete', args=[payment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'

    def test_fail_payment(self, admin_client, payment):
        """Test marking payment as failed."""
        url = reverse('payments:payment-fail', args=[payment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'failed'

    def test_complete_already_completed_payment(self, admin_client, payment):
        """Test completing an already completed payment fails."""
        payment.status = Payment.Status.COMPLETED
        payment.save()

        url = reverse('payments:payment-complete', args=[payment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for Payment model."""

    def test_payment_str(self, payment):
        """Test payment string representation."""
        assert f'Payment #{payment.id}' in str(payment)
        assert str(payment.amount) in str(payment)

    def test_remaining_amount(self, payment, order):
        """Test remaining amount calculation."""
        OrderPayment.objects.create(
            order=order,
            payment=payment,
            amount_applied=Decimal('50.00')
        )

        assert payment.remaining_amount == Decimal('150.00')

    def test_amount_applied(self, payment, order):
        """Test amount applied calculation."""
        OrderPayment.objects.create(
            order=order,
            payment=payment,
            amount_applied=Decimal('75.00')
        )

        assert payment.amount_applied == Decimal('75.00')
