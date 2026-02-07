"""
Tests for the users app.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration."""

    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'
        assert User.objects.filter(email='newuser@example.com').exists()

    def test_register_user_password_mismatch(self, api_client):
        """Test registration fails with password mismatch."""
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_register_user_duplicate_email(self, api_client, user):
        """Test registration fails with duplicate email."""
        url = reverse('users:register')
        data = {
            'email': user.email,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Tests for user login."""

    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = reverse('users:login')
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self, api_client, user):
        """Test login fails with invalid credentials."""
        url = reverse('users:login')
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserLogout:
    """Tests for user logout."""

    def test_logout_success(self, api_client, user):
        """Test successful logout."""
        # First login to get tokens
        login_url = reverse('users:login')
        login_data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']

        # Logout
        logout_url = reverse('users:logout')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.post(logout_url, {'refresh': refresh_token})

        assert response.status_code == status.HTTP_200_OK

    def test_logout_without_token(self, authenticated_client):
        """Test logout fails without refresh token."""
        url = reverse('users:logout')
        response = authenticated_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile."""

    def test_get_profile(self, authenticated_client, user):
        """Test get user profile."""
        url = reverse('users:profile')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_update_profile(self, authenticated_client, user):
        """Test update user profile."""
        url = reverse('users:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'

    def test_profile_unauthenticated(self, api_client):
        """Test profile access requires authentication."""
        url = reverse('users:profile')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
