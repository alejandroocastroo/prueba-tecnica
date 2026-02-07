"""
Tests for the chatbot app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from apps.shipments.models import Shipment
from apps.payments.models import Payment, OrderPayment
from .agent import EcommerceAgent


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
    order = Order.objects.create(user=user, status=Order.Status.PAID)
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=product.price
    )
    order.calculate_total()
    return order


@pytest.fixture
def shipment(db, order):
    """Create a test shipment."""
    shipment = Shipment.objects.create(order=order)
    shipment.mark_as_shipped()
    return shipment


@pytest.fixture
def payment(db, order):
    """Create a test payment applied to an order."""
    payment = Payment.objects.create(
        amount=Decimal('200.00'),
        method=Payment.Method.CARD,
        status=Payment.Status.COMPLETED
    )
    OrderPayment.objects.create(
        order=order,
        payment=payment,
        amount_applied=Decimal('200.00')
    )
    return payment


@pytest.mark.django_db
class TestChatEndpoint:
    """Tests for the chat endpoint."""

    @patch.object(EcommerceAgent, 'chat')
    def test_chat_success(self, mock_chat, authenticated_client):
        """Test successful chat request."""
        mock_chat.return_value = "Your order #1 is currently in 'Paid' status."

        url = reverse('chatbot:chat')
        data = {'message': 'What is the status of my order 1?'}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'response' in response.data
        assert 'user_message' in response.data
        mock_chat.assert_called_once()

    def test_chat_empty_message(self, authenticated_client):
        """Test chat with empty message."""
        url = reverse('chatbot:chat')
        data = {'message': '   '}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_chat_unauthenticated(self, api_client):
        """Test chat requires authentication."""
        url = reverse('chatbot:chat')
        data = {'message': 'Hello'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAgentTools:
    """Tests for agent tool functions."""

    def test_get_order_status(self, user, order):
        """Test getting order status."""
        agent = EcommerceAgent(user)
        result = agent.get_order_status(order.id)

        assert result['found'] is True
        assert result['order_id'] == order.id
        assert result['status'] == 'Paid'
        assert len(result['items']) == 1

    def test_get_order_status_not_found(self, user):
        """Test getting non-existent order status."""
        agent = EcommerceAgent(user)
        result = agent.get_order_status(99999)

        assert result['found'] is False
        assert 'error' in result

    def test_get_order_status_wrong_user(self, user, admin_user, order):
        """Test getting order that belongs to another user."""
        agent = EcommerceAgent(admin_user)
        result = agent.get_order_status(order.id)

        assert result['found'] is False

    def test_get_shipment_info(self, user, order, shipment):
        """Test getting shipment info."""
        agent = EcommerceAgent(user)
        result = agent.get_shipment_info(order.id)

        assert result['found'] is True
        assert len(result['shipments']) == 1
        assert result['shipments'][0]['status'] == 'Shipped'
        assert result['shipments'][0]['tracking_number'] is not None

    def test_get_shipment_info_no_shipments(self, user, product):
        """Test getting shipment info when no shipments exist."""
        order = Order.objects.create(user=user, status=Order.Status.PAID)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=product.price
        )

        agent = EcommerceAgent(user)
        result = agent.get_shipment_info(order.id)

        assert result['found'] is True
        assert result['shipments'] == []
        assert 'message' in result

    def test_get_payment_info(self, user, order, payment):
        """Test getting payment info."""
        agent = EcommerceAgent(user)
        result = agent.get_payment_info(order.id)

        assert result['found'] is True
        assert result['order_total'] == '200.00'
        assert result['total_paid'] == '200.00'
        assert len(result['payments']) == 1

    def test_get_payment_info_no_payments(self, user, product):
        """Test getting payment info when no payments exist."""
        order = Order.objects.create(user=user, status=Order.Status.PENDING)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=product.price
        )
        order.calculate_total()

        agent = EcommerceAgent(user)
        result = agent.get_payment_info(order.id)

        assert result['found'] is True
        assert result['payments'] == []
        assert 'message' in result

    def test_list_user_orders(self, user, order):
        """Test listing user orders."""
        agent = EcommerceAgent(user)
        result = agent.list_user_orders()

        assert 'orders' in result
        assert len(result['orders']) >= 1
        assert result['orders'][0]['order_id'] == order.id

    def test_list_user_orders_empty(self, admin_user):
        """Test listing orders when user has none."""
        agent = EcommerceAgent(admin_user)
        result = agent.list_user_orders()

        assert result['orders'] == []
        assert 'message' in result


@pytest.mark.django_db
class TestAgentChat:
    """Tests for agent chat functionality."""

    @patch('apps.chatbot.agent.anthropic.Anthropic')
    def test_chat_with_mocked_api(self, mock_anthropic, user, order):
        """Test chat with mocked Anthropic API."""
        # Setup mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Your order status is Paid.", type="text")]
        mock_response.content[0].text = "Your order status is Paid."
        mock_client.messages.create.return_value = mock_response

        with patch('apps.chatbot.agent.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = 'test-key'

            agent = EcommerceAgent(user)
            result = agent.chat("What is my order status?")

            assert "Paid" in result or result == "Your order status is Paid."

    def test_chat_without_api_key(self, user):
        """Test chat when API key is not configured."""
        with patch('apps.chatbot.agent.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ''

            agent = EcommerceAgent(user)
            result = agent.chat("Hello")

            assert "not configured" in result
