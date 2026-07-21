from django.urls import path

from . import views

urlpatterns = [
    path('brands/', views.BrandListView.as_view()),
    path('products/', views.ProductListView.as_view()),
    path('products/<int:product_id>/', views.ProductDetailView.as_view()),
]
