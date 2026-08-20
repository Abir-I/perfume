"""Canonical cart models.

The old project contained a second cart implementation based on Django's
built-in auth.User and tables named cart_cart/cart_cart_item.  The real
schema uses ``cart`` and ``cart_item`` with accounts.User, so the canonical
models live in accounts.models and are re-exported here for compatibility.
"""
from accounts.models import Cart, CartItem

__all__ = ['Cart', 'CartItem']
