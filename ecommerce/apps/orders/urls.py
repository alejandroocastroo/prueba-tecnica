"""
URL patterns for the orders app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet

app_name = 'orders'

router = DefaultRouter()
router.register('', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
