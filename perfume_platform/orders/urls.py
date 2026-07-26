from django.urls import path

from .views import CheckoutView, OrderDetailView, OrderListView

urlpatterns = [
    path('checkout/', CheckoutView.as_view()),        # POST /api/orders/checkout/
    path('<int:order_id>/', OrderDetailView.as_view()),  # GET  /api/orders/{order_id}/
    path('', OrderListView.as_view()),                 # GET  /api/orders/
]
