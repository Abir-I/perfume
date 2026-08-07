from django.urls import path
from accounts.views import LoginView, RegisterView
from .views import (
    BrandListView,
    ProductListView,
    ProductDetailView,
    PerfumeDetailView
)
from .admin_views import (
    AdminProductListView,
    AdminPerfumeCreateView,
    AdminPerfumeUpdateView,
    AdminProductDeleteView,
)
from .detail_views import (
    ProductFullDetailView,
    ProductBySlugView,
    RelatedProductsView,
    ProductReviewsView,
    StorefrontCartView,
    StorefrontCartAddView,
    StorefrontCartUpdateView,
    WishlistView,
    RecentlyViewedView,
)
from .admin_views_premium import (
    AdminProductListView as AdminProductListPremiumView,
    AdminProductDetailView,
    AdminUpdateDiscountView,
    AdminUpdateStockView,
    AdminUpdateFeaturesView,
    AdminDashboardStatsView,
    AdminBulkOperationView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('perfumes/<int:perfume_id>/', PerfumeDetailView.as_view(), name='perfume-detail'),

    # ── Product Details page (dynamic, one page for every product) ──
    path('products/<int:product_id>/detail/', ProductFullDetailView.as_view(), name='product-full-detail'),
    path('products/<int:product_id>/related/', RelatedProductsView.as_view(), name='product-related'),
    path('products/<int:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/by-slug/<slug:slug>/', ProductBySlugView.as_view(), name='product-by-slug'),

    # Storefront cart / wishlist / recently viewed (AJAX)
    path('cart/', StorefrontCartView.as_view(), name='storefront-cart'),
    path('cart/add/', StorefrontCartAddView.as_view(), name='storefront-cart-add'),
    path('cart/update/', StorefrontCartUpdateView.as_view(), name='storefront-cart-update'),
    path('wishlist/', WishlistView.as_view(), name='storefront-wishlist'),
    path('recently-viewed/', RecentlyViewedView.as_view(), name='storefront-recently-viewed'),

    # Admin dashboard endpoints
    path('admin/products/', AdminProductListView.as_view(), name='admin-product-list'),
    path('admin/perfumes/', AdminPerfumeCreateView.as_view(), name='admin-perfume-create'),
    path('admin/perfumes/<int:perfume_id>/', AdminPerfumeUpdateView.as_view(), name='admin-perfume-update'),
    path('admin/products/<int:product_id>/', AdminProductDeleteView.as_view(), name='admin-product-delete'),
    
    # Premium admin endpoints
    path('admin/premium/products/', AdminProductListPremiumView.as_view(), name='admin-premium-products'),
    path('admin/premium/products/<int:product_id>/', AdminProductDetailView.as_view(), name='admin-premium-product-detail'),
    path('admin/premium/products/<int:product_id>/update-discount/', AdminUpdateDiscountView.as_view(), name='admin-update-discount'),
    path('admin/premium/products/<int:product_id>/update-stock/', AdminUpdateStockView.as_view(), name='admin-update-stock'),
    path('admin/premium/products/<int:product_id>/update-features/', AdminUpdateFeaturesView.as_view(), name='admin-update-features'),
    path('admin/premium/stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('admin/premium/bulk-operation/', AdminBulkOperationView.as_view(), name='admin-bulk-operation'),
]