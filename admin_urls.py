from django.urls import path

from . import admin_views

urlpatterns = [
    path('perfumes/', admin_views.PerfumeAdminCreateView.as_view()),
    path('perfumes/<int:perfume_id>/', admin_views.PerfumeAdminDetailView.as_view()),
    path('perfumes/<int:perfume_id>/variants/', admin_views.ProductVariantCreateView.as_view()),
    path('perfumes/<int:perfume_id>/image/', admin_views.ProductImageUploadView.as_view()),
    path('products/<int:product_id>/', admin_views.ProductVariantDetailView.as_view()),
    path('search/', admin_views.AdminProductSearchView.as_view()),
]
