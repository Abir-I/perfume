"""
Orders Admin Interface
"""

from django.contrib import admin
from .models import CustomerOrder, OrderItem, OrderTracking, Payment, Invoice


class OrderItemInline(admin.TabularInline):
    """Inline order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_brand', 'quantity', 'unit_price', 'total_price')
    fields = ('product_name', 'product_brand', 'quantity', 'unit_price', 'total_price')
    can_delete = False


class OrderTrackingInline(admin.TabularInline):
    """Inline tracking history"""
    model = OrderTracking
    extra = 1
    fields = ('status', 'status_message', 'location', 'timestamp')


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    """Customer order admin"""
    list_display = ('order_number', 'customer_name', 'order_status', 'payment_status', 'total_amount', 'order_date')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    list_filter = ('order_status', 'payment_status', 'order_date')
    readonly_fields = ('order_number', 'order_date', 'updated_at', 'tracking_number')
    inlines = [OrderItemInline, OrderTrackingInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'order_date', 'updated_at', 'order_status')
        }),
        ('Customer Info', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'courier_name', 'courier_url', 'estimated_delivery', 'shipped_date', 'delivered_date')
        }),
        ('Cancellation', {
            'fields': ('is_cancelled', 'cancellation_reason', 'cancelled_date'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('order_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Order item admin"""
    list_display = ('product_name', 'order', 'quantity', 'unit_price', 'total_price')
    search_fields = ('product_name', 'order__order_number')
    readonly_fields = ('product_name', 'product_brand', 'quantity', 'unit_price', 'total_price')


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    """Order tracking admin"""
    list_display = ('order', 'status', 'status_message', 'location', 'timestamp')
    search_fields = ('order__order_number', 'status_message')
    list_filter = ('status', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin"""
    list_display = ('order', 'payment_method', 'amount', 'payment_status', 'payment_date')
    search_fields = ('order__order_number', 'transaction_id')
    list_filter = ('payment_status', 'payment_method', 'payment_date')
    readonly_fields = ('payment_date', 'refund_date')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Invoice admin"""
    list_display = ('invoice_number', 'order', 'total', 'invoice_date')
    search_fields = ('invoice_number', 'order__order_number')
    readonly_fields = ('invoice_number', 'invoice_date')
