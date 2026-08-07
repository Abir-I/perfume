from django.urls import path

from . import admin_views

urlpatterns = [
    path('perfumes/', admin_views.AdminPerfumeCreateView.as_view()),
    path('perfumes/<int:perfume_id>/', admin_views.AdminPerfumeDetailView.as_view()),
    path('perfumes/<int:perfume_id>/variants/', admin_views.AdminVariantCreateView.as_view()),
    path('perfumes/<int:perfume_id>/image/', admin_views.AdminImageUploadView.as_view()),
    path('products/<int:product_id>/', admin_views.AdminVariantDetailView.as_view()),
    path('inventory/', admin_views.AdminInventoryView.as_view()),
    path('search/', admin_views.AdminSearchView.as_view()),
]
