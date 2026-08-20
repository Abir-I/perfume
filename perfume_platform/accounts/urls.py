from django.urls import path
from .views import RegisterView, LoginView
from .dashboard_views import (
    DashboardView,
    ProfileView,
    OrdersListView,
    OrderDetailView,
    OrderTrackingView,
    OrderCancelView,
    ReviewsListView,
    ReviewCreateView,
    ReviewUpdateView,
    ReviewDeleteView,
    WishlistView,
    WishlistAddView,
    WishlistRemoveView,
    AddressesView,
    SettingsView,
    ActivityView,
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Dashboard & Profile
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Orders
    path('orders/', OrdersListView.as_view(), name='orders-list'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/tracking/', OrderTrackingView.as_view(), name='order-tracking'),
    path('orders/<int:order_id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    
    # Reviews
    path('reviews/', ReviewsListView.as_view(), name='reviews-list'),
    path('reviews/create/', ReviewCreateView.as_view(), name='review-create'),
    path('reviews/<int:review_id>/update/', ReviewUpdateView.as_view(), name='review-update'),
    path('reviews/<int:review_id>/delete/', ReviewDeleteView.as_view(), name='review-delete'),
    
    # Wishlist
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/', WishlistAddView.as_view(), name='wishlist-add'),
    path('wishlist/<int:product_id>/remove/', WishlistRemoveView.as_view(), name='wishlist-remove'),
    
    # Addresses
    path('addresses/', AddressesView.as_view(), name='addresses'),
    
    # Settings
    path('settings/', SettingsView.as_view(), name='settings'),
    
    # Activity
    path('activity/', ActivityView.as_view(), name='activity'),
]
