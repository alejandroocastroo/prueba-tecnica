"""
Tests for the orders app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from apps.products.models import Product
from .models import Order, OrderItem


@pytest.fixture
def product(db):
    """Create a test product."""
    return Product.objects.create(
        name='Test Product',
        description='Test description',
        price=Decimal('100.00'),
        stock=10,
        is_active=True
    )


@pytest.fixture
def product2(db):
    """Create a second test product."""
    return Product.objects.create(
        name='Second Product',
        description='Another description',
        price=Decimal('50.00'),
        stock=5,
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


@pytest.mark.django_db
class TestOrderCreation:
    """Tests for order creation."""

    def test_create_order_success(self, authenticated_client, product, product2):
        """Test successful order creation."""
        url = reverse('orders:order-list')
        data = {
            'items': [
                {'product_id': product.id, 'quantity': 2},
                {'product_id': product2.id, 'quantity': 1}
            ]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert Decimal(response.data['total']) == Decimal('250.00')  # 2*100 + 1*50
        assert len(response.data['items']) == 2

        # Check stock was reduced
        product.refresh_from_db()
        product2.refresh_from_db()
        assert product.stock == 8
        assert product2.stock == 4

    def test_create_order_empty_items(self, authenticated_client):
        """Test order creation fails with empty items."""
        url = reverse('orders:order-list')
        data = {'items': []}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_insufficient_stock(self, authenticated_client, product):
        """Test order creation fails with insufficient stock."""
        url = reverse('orders:order-list')
        data = {
            'items': [
                {'product_id': product.id, 'quantity': 100}  # More than stock
            ]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Insufficient stock' in str(response.data)

    def test_create_order_duplicate_products(self, authenticated_client, product):
        """Test order creation fails with duplicate products."""
        url = reverse('orders:order-list')
        data = {
            'items': [
                {'product_id': product.id, 'quantity': 1},
                {'product_id': product.id, 'quantity': 2}
            ]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_unauthenticated(self, api_client, product):
        """Test order creation requires authentication."""
        url = reverse('orders:order-list')
        data = {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrderList:
    """Tests for order listing."""

    def test_list_own_orders(self, authenticated_client, order):
        """Test listing user's own orders."""
        url = reverse('orders:order-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_list_all_orders_as_admin(self, admin_client, order):
        """Test admin can see all orders."""
        url = reverse('orders:order-list')
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_my_orders_endpoint(self, authenticated_client, order):
        """Test the my-orders endpoint."""
        url = reverse('orders:order-my-orders')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestOrderDetail:
    """Tests for order detail."""

    def test_get_order_detail(self, authenticated_client, order):
        """Test getting order details."""
        url = reverse('orders:order-detail', args=[order.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == order.id
        assert len(response.data['items']) == 1


@pytest.mark.django_db
class TestOrderStatusUpdate:
    """Tests for order status update."""

    def test_update_status_valid_transition(self, admin_client, order):
        """Test valid status transition."""
        url = reverse('orders:order-update-status', args=[order.id])
        data = {'status': 'paid'}

        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'paid'

    def test_update_status_invalid_transition(self, admin_client, order):
        """Test invalid status transition."""
        url = reverse('orders:order-update-status', args=[order.id])
        data = {'status': 'delivered'}  # Can't go from pending to delivered

        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOrderModel:
    """Tests for Order model."""

    def test_order_str(self, order, user):
        """Test order string representation."""
        assert f'Order #{order.id}' in str(order)
        assert user.email in str(order)

    def test_calculate_total(self, order, product):
        """Test total calculation."""
        expected_total = Decimal('200.00')  # 2 * 100.00
        assert order.total == expected_total

    def test_order_item_subtotal(self, order):
        """Test order item subtotal calculation."""
        item = order.items.first()
        assert item.subtotal == Decimal('200.00')
