"""Canonical order integration around the existing MySQL order tables.

The existing customer_order/order_item/payment/invoice tables remain the
single source of truth for the core order.  The small managed snapshot/history
tables below add information that the legacy schema cannot safely preserve:
shipping-address snapshots, purchase-time financials/item snapshots, and
status history.
"""
from django.db import models
from django.utils import timezone
from accounts.models import CustomerOrder, OrderItem, Payment, Invoice, User


class OrderStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    CONFIRMED = 'Confirmed', 'Confirmed'
    PROCESSING = 'Processing', 'Processing'
    SHIPPED = 'Shipped', 'Shipped'
    DELIVERED = 'Delivered', 'Delivered'
    CANCELLED = 'Cancelled', 'Cancelled'


class PaymentStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    COMPLETED = 'Completed', 'Completed'
    FAILED = 'Failed', 'Failed'
    REFUNDED = 'Refunded', 'Refunded'


class OrderShippingSnapshot(models.Model):
    snapshot_id = models.BigAutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, db_column='order_id', related_name='shipping_snapshot')
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order_shipping_snapshot'
        ordering = ['snapshot_id']


class OrderFinancialSnapshot(models.Model):
    snapshot_id = models.BigAutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, db_column='order_id', related_name='financial_snapshot')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order_financial_snapshot'


class OrderItemSnapshot(models.Model):
    snapshot_id = models.BigAutoField(primary_key=True)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, db_column='order_item_id', related_name='purchase_snapshot')
    product_name = models.CharField(max_length=200)
    brand_name = models.CharField(max_length=150, blank=True)
    product_type = models.CharField(max_length=30)
    volume_ml = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    image_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order_item_snapshot'


class ReturnStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'
    RECEIVED = 'Received', 'Received'
    REFUNDED = 'Refunded', 'Refunded'
    CANCELLED = 'Cancelled', 'Cancelled'


class ReturnRequest(models.Model):
    return_id = models.BigAutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, db_column='order_id', related_name='return_request')
    reason = models.CharField(max_length=100)
    details = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=ReturnStatus.choices, default=ReturnStatus.PENDING)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    admin_note = models.CharField(max_length=500, blank=True, default='')
    requested_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'return_request'
        ordering = ['-requested_at']


class OrderStatusHistory(models.Model):
    history_id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, db_column='order_id', related_name='status_history')
    status = models.CharField(max_length=10)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='changed_by')
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order_status_history'
        ordering = ['created_at', 'history_id']


__all__ = [
    'CustomerOrder', 'OrderItem', 'Payment', 'Invoice',
    'OrderStatus', 'PaymentStatus',
    'OrderShippingSnapshot', 'OrderFinancialSnapshot',
    'OrderItemSnapshot', 'OrderStatusHistory', 'ReturnStatus', 'ReturnRequest',
]
