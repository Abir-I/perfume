"""
Orders Models - Complete Order Management System
"""

from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product


class OrderStatus(models.TextChoices):
    """Order Status Choices"""
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    PROCESSING = 'processing', 'Processing'
    SHIPPED = 'shipped', 'Shipped'
    IN_TRANSIT = 'in_transit', 'In Transit'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    RETURNED = 'returned', 'Returned'


class PaymentStatus(models.TextChoices):
    """Payment Status Choices"""
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'


class CustomerOrder(models.Model):
    """Customer Order Model"""
    
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Order Info
    order_number = models.CharField(max_length=50, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Customer Info
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Shipping Info
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=50)
    shipping_state = models.CharField(max_length=50)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=50, default='Bangladesh')
    
    # Order Status
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cod', 'Cash on Delivery'),
            ('card', 'Credit/Debit Card'),
            ('bkash', 'bKash'),
            ('nagad', 'Nagad'),
        ],
        default='cod'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    delivered_date = models.DateTimeField(blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True)
    courier_url = models.URLField(blank=True, null=True)
    
    # Notes
    order_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Cancellation
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    cancelled_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'orders_customer_order'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['user', '-order_date']),
            models.Index(fields=['order_status']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.order_status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    def get_status_display_fancy(self):
        """Get fancy status display"""
        status_map = {
            'pending': '⏳ Pending',
            'confirmed': '✅ Confirmed',
            'processing': '🔄 Processing',
            'shipped': '📦 Shipped',
            'in_transit': '🚚 In Transit',
            'out_for_delivery': '🚪 Out for Delivery',
            'delivered': '🎉 Delivered',
            'cancelled': '❌ Cancelled',
            'returned': '🔄 Returned',
        }
        return status_map.get(self.order_status, self.order_status)


class OrderItem(models.Model):
    """Individual items in an order"""
    
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    product_name = models.CharField(max_length=255)
    product_brand = models.CharField(max_length=100)
    product_image = models.URLField(blank=True)
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'orders_order_item'
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OrderTracking(models.Model):
    """Order Tracking History"""
    
    tracking_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='tracking_history')
    
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    status_message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'orders_order_tracking'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


class Payment(models.Model):
    """Payment Information"""
    
    payment_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, related_name='payment')
    
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    payment_date = models.DateTimeField(blank=True, null=True)
    refund_date = models.DateTimeField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'orders_payment'
    
    def __str__(self):
        return f"Payment for Order #{self.order.order_number}"


class Invoice(models.Model):
    """Invoice for Order"""
    
    invoice_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, related_name='invoice')
    
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'orders_invoice'
    
    def __str__(self):
        return f"Invoice #{self.invoice_number}"
