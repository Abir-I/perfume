"""
Cart URLs
"""

from django.urls import path
from .views import (
    CartListView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    ClearCartView,
)

urlpatterns = [
    path('', CartListView.as_view(), name='cart-list'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('items/<int:item_id>/update/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('items/<int:item_id>/remove/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('clear/', ClearCartView.as_view(), name='clear-cart'),
]
