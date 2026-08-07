"""
Orders URLs
"""

from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    CancelOrderView,
    CheckoutView,
)

urlpatterns = [
    # Orders
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='order-cancel'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]
