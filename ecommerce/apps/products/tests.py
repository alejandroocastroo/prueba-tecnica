"""
Tests for the products app.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from .models import Product


@pytest.fixture
def product(db):
    """Create a test product."""
    return Product.objects.create(
        name='Test Product',
        description='Test description',
        price=Decimal('99.99'),
        stock=10,
        is_active=True
    )


@pytest.fixture
def inactive_product(db):
    """Create an inactive product."""
    return Product.objects.create(
        name='Inactive Product',
        description='Inactive',
        price=Decimal('49.99'),
        stock=5,
        is_active=False
    )


@pytest.mark.django_db
class TestProductList:
    """Tests for product listing."""

    def test_list_products(self, api_client, product):
        """Test listing products without authentication."""
        url = reverse('products:product-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_list_products_filter_by_active(self, api_client, product, inactive_product):
        """Test filtering products by active status."""
        url = reverse('products:product-list')
        response = api_client.get(url, {'is_active': 'true'})

        assert response.status_code == status.HTTP_200_OK
        for p in response.data['results']:
            assert p['is_active'] is True

    def test_search_products(self, api_client, product):
        """Test searching products."""
        url = reverse('products:product-list')
        response = api_client.get(url, {'search': 'Test'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestProductDetail:
    """Tests for product detail."""

    def test_get_product_detail(self, api_client, product):
        """Test retrieving product details."""
        url = reverse('products:product-detail', args=[product.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Product'
        assert response.data['is_in_stock'] is True


@pytest.mark.django_db
class TestProductCreate:
    """Tests for product creation."""

    def test_create_product_as_admin(self, admin_client):
        """Test creating product as admin."""
        url = reverse('products:product-list')
        data = {
            'name': 'New Product',
            'description': 'New product description',
            'price': '149.99',
            'stock': 20,
            'is_active': True
        }

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Product'
        assert Product.objects.filter(name='New Product').exists()

    def test_create_product_as_regular_user(self, authenticated_client):
        """Test that regular users cannot create products."""
        url = reverse('products:product-list')
        data = {
            'name': 'New Product',
            'description': 'Description',
            'price': '49.99',
            'stock': 5
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_invalid_price(self, admin_client):
        """Test creating product with invalid price."""
        url = reverse('products:product-list')
        data = {
            'name': 'New Product',
            'price': '-10.00',
            'stock': 5
        }

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProductUpdate:
    """Tests for product update."""

    def test_update_product_as_admin(self, admin_client, product):
        """Test updating product as admin."""
        url = reverse('products:product-detail', args=[product.id])
        data = {'name': 'Updated Product Name'}

        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Product Name'

    def test_update_product_as_regular_user(self, authenticated_client, product):
        """Test that regular users cannot update products."""
        url = reverse('products:product-detail', args=[product.id])
        data = {'name': 'Updated Name'}

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductDelete:
    """Tests for product deletion."""

    def test_delete_product_as_admin(self, admin_client, product):
        """Test deleting product as admin."""
        url = reverse('products:product-detail', args=[product.id])
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Product.objects.filter(id=product.id).exists()

    def test_delete_product_as_regular_user(self, authenticated_client, product):
        """Test that regular users cannot delete products."""
        url = reverse('products:product-detail', args=[product.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model."""

    def test_product_str(self, product):
        """Test product string representation."""
        assert str(product) == 'Test Product'

    def test_is_in_stock_true(self, product):
        """Test is_in_stock property when stock > 0."""
        assert product.is_in_stock is True

    def test_is_in_stock_false(self, db):
        """Test is_in_stock property when stock = 0."""
        product = Product.objects.create(
            name='Out of Stock',
            price=Decimal('10.00'),
            stock=0
        )
        assert product.is_in_stock is False
