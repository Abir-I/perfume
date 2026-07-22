from django.urls import path
from accounts.views import LoginView, RegisterView
from .views import (
    BrandListView,
    ProductListView,
    ProductDetailView,
    PerfumeDetailView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('perfumes/<int:perfume_id>/', PerfumeDetailView.as_view(), name='perfume-detail'),
]