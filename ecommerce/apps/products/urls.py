"""
URL patterns for the products app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet

app_name = 'products'

router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
