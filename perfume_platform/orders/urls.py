from django.urls import path
from .views import OrderListView, OrderDetailView, CancelOrderView, CheckoutView, OrderTrackingView, InvoiceView, ReturnRequestListView, ReturnRequestView
from .admin_api import AdminOrderListView, AdminOrderDetailView, AdminOrderStatusUpdateView, AdminOrderStatsView, AdminReturnListView, AdminReturnStatusUpdateView

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('returns/', ReturnRequestListView.as_view(), name='return-list'),
    path('<int:order_id>/tracking/', OrderTrackingView.as_view(), name='order-tracking'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='order-cancel'),
    path('<int:order_id>/return/', ReturnRequestView.as_view(), name='order-return'),
    path('<int:order_id>/invoice/', InvoiceView.as_view(), name='order-invoice'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('admin/stats/', AdminOrderStatsView.as_view(), name='admin-order-stats'),
    path('admin/returns/', AdminReturnListView.as_view(), name='admin-return-list'),
    path('admin/returns/<int:return_id>/status/', AdminReturnStatusUpdateView.as_view(), name='admin-return-status'),
    path('admin/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/<int:order_id>/status/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status'),
]
