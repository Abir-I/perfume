from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [
    path('', lambda request: render(request, 'home.html')),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
]