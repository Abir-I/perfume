"""Canonical catalog models.

The database schema is owned by ``accounts.models`` because the existing
MySQL tables are shared by the customer, cart and order APIs.  Re-exporting
those classes here prevents Django from creating a second set of model
classes for the same tables.
"""
from accounts.models import Brand, Perfume, Product, BulkBottle, Review

__all__ = ['Brand', 'Perfume', 'Product', 'BulkBottle', 'Review']
