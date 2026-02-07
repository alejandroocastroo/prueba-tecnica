"""
URL patterns for the shipments app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ShipmentViewSet

app_name = 'shipments'

router = DefaultRouter()
router.register('', ShipmentViewSet, basename='shipment')

urlpatterns = [
    path('', include(router.urls)),
]
