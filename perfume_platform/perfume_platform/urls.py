from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [
    path('', lambda request: render(request, 'home.html')),
    path('shop/', lambda request: render(request, 'shop.html')),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/catalog/', include('catalog.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
]