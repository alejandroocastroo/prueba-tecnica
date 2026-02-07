"""
Tests for the shipments app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from .models import Shipment


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
def paid_order(db, user, product):
    """Create a paid order."""
    order = Order.objects.create(user=user, status=Order.Status.PAID)
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=product.price
    )
    order.calculate_total()
    return order


@pytest.fixture
def shipment(db, paid_order):
    """Create a test shipment."""
    return Shipment.objects.create(order=paid_order)


@pytest.mark.django_db
class TestShipmentCreation:
    """Tests for shipment creation."""

    def test_create_shipment_success(self, admin_client, paid_order):
        """Test successful shipment creation."""
        url = reverse('shipments:shipment-list')
        data = {'order_id': paid_order.id}

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert Shipment.objects.filter(order=paid_order).exists()

    def test_create_shipment_unpaid_order(self, admin_client, user, product):
        """Test shipment creation fails for unpaid order."""
        order = Order.objects.create(user=user, status=Order.Status.PENDING)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=product.price
        )

        url = reverse('shipments:shipment-list')
        data = {'order_id': order.id}

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_shipment_regular_user_forbidden(self, authenticated_client, paid_order):
        """Test regular users cannot create shipments."""
        url = reverse('shipments:shipment-list')
        data = {'order_id': paid_order.id}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestShipmentStatus:
    """Tests for shipment status changes."""

    @patch('apps.shipments.views.send_shipment_notification.delay')
    def test_ship_shipment(self, mock_notification, admin_client, shipment):
        """Test marking shipment as shipped."""
        url = reverse('shipments:shipment-ship', args=[shipment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'shipped'
        assert response.data['tracking_number'] is not None
        assert response.data['shipped_at'] is not None

        mock_notification.assert_called_once_with(shipment.id, 'shipped')

        shipment.order.refresh_from_db()
        assert shipment.order.status == 'shipped'

    @patch('apps.shipments.views.send_shipment_notification.delay')
    def test_deliver_shipment(self, mock_notification, admin_client, shipment):
        """Test marking shipment as delivered."""
        # First ship it
        shipment.mark_as_shipped()

        url = reverse('shipments:shipment-deliver', args=[shipment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'delivered'
        assert response.data['delivered_at'] is not None

        mock_notification.assert_called_once_with(shipment.id, 'delivered')

        shipment.order.refresh_from_db()
        assert shipment.order.status == 'delivered'

    def test_ship_non_pending_shipment(self, admin_client, shipment):
        """Test shipping non-pending shipment fails."""
        shipment.status = Shipment.Status.SHIPPED
        shipment.save()

        url = reverse('shipments:shipment-ship', args=[shipment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deliver_non_shipped_shipment(self, admin_client, shipment):
        """Test delivering non-shipped shipment fails."""
        url = reverse('shipments:shipment-deliver', args=[shipment.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestShipmentTracking:
    """Tests for shipment tracking."""

    def test_track_by_tracking_number(self, authenticated_client, shipment):
        """Test tracking shipment by tracking number."""
        shipment.mark_as_shipped()

        url = reverse('shipments:shipment-track', args=[shipment.tracking_number])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tracking_number'] == shipment.tracking_number

    def test_track_nonexistent_tracking_number(self, authenticated_client):
        """Test tracking with nonexistent tracking number."""
        url = reverse('shipments:shipment-track', args=['FAKE-TRACKING'])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestShipmentByOrder:
    """Tests for getting shipments by order."""

    def test_get_shipments_by_order(self, authenticated_client, shipment):
        """Test getting shipments for a specific order."""
        url = reverse('shipments:shipment-by-order', args=[shipment.order_id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestShipmentModel:
    """Tests for Shipment model."""

    def test_shipment_str(self, shipment):
        """Test shipment string representation."""
        assert f'Shipment #{shipment.id}' in str(shipment)
        assert f'Order #{shipment.order_id}' in str(shipment)

    def test_generate_tracking_number(self, shipment):
        """Test tracking number generation."""
        tracking = shipment.generate_tracking_number()

        assert tracking.startswith('TRK-')
        assert len(tracking) == 16  # TRK- + 12 chars
        assert shipment.tracking_number == tracking
