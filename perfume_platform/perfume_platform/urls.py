from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from catalog.page_views import product_detail_page, product_detail_redirect

urlpatterns = [
    # Main Pages
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('shop/', TemplateView.as_view(template_name='shop.html'), name='shop'),
    # ── Dynamic Product Details page (one page for every product) ──
    path('product/<slug:slug>/<int:product_id>/', product_detail_page, name='product-detail'),
    path('product/<int:product_id>/', product_detail_page, name='product-detail-by-id'),
    path('product/<slug:slug>/', product_detail_page, name='product-detail-by-slug'),
    path('products/', product_detail_redirect, name='product-detail-legacy'),
    path('brands/', TemplateView.as_view(template_name='brands.html'), name='brands'),
    path('decants/', TemplateView.as_view(template_name='decants.html'), name='decants'),
    
    # Shopping & Checkout
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart'),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('order-tracking/', TemplateView.as_view(template_name='order_tracking.html'), name='order-tracking'),
    
    # Customer Dashboard (PRODUCTION) - Multiple paths
    path('dashboard/', TemplateView.as_view(template_name='customer_dashboard.html'), name='dashboard'),
    path('account/', TemplateView.as_view(template_name='customer_dashboard.html'), name='account'),
    path('my-account/', TemplateView.as_view(template_name='customer_dashboard.html'), name='my-account'),
    path('customer/', TemplateView.as_view(template_name='customer_dashboard.html'), name='customer-dashboard'),
    
    # Admin Panel
    path('admin/', admin.site.urls),
    path('admin-dashboard/', TemplateView.as_view(template_name='admin.html'), name='admin-dashboard'),
    path('admin-premium/', RedirectView.as_view(url='/admin-dashboard/', permanent=False), name='admin-premium-dashboard'),
    path('admin-orders/', TemplateView.as_view(template_name='admin_orders.html'), name='admin-orders'),
    path('order-confirmation/', TemplateView.as_view(template_name='order_confirmation.html'), name='order-confirmation'),
    path('invoice/', TemplateView.as_view(template_name='invoice.html'), name='invoice-page'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/catalog/', include('catalog.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
