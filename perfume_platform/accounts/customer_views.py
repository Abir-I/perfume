"""Compatibility aliases for the canonical customer dashboard API."""
from .dashboard_views import (
    ProfileView as CustomerProfileView,
    OrdersListView as CustomerOrdersView,
    OrderDetailView as CustomerOrderDetailView,
    AddressesView as CustomerAddressesView,
    WishlistView as CustomerWishlistView,
    WishlistAddView as CustomerWishlistAddView,
    WishlistRemoveView as CustomerWishlistRemoveView,
    ReviewsListView as CustomerReviewsView,
    ReviewCreateView as CustomerReviewCreateView,
    ReviewUpdateView as CustomerReviewUpdateView,
    ReviewDeleteView as CustomerReviewDeleteView,
)
