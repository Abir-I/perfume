from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin
from .models import OrderShippingSnapshot, OrderFinancialSnapshot, OrderItemSnapshot, OrderStatusHistory, ReturnRequest, ReturnStatus


@admin.register(OrderShippingSnapshot)
class OrderShippingSnapshotAdmin(ModelAdmin):
    list_display = ('snapshot_id', 'order', 'name', 'phone', 'city', 'country', 'created_at')
    search_fields = ('order__order_id', 'name', 'email', 'phone', 'city')
    readonly_fields = tuple(f.name for f in OrderShippingSnapshot._meta.fields)


@admin.register(OrderFinancialSnapshot)
class OrderFinancialSnapshotAdmin(ModelAdmin):
    list_display = ('snapshot_id', 'order', 'subtotal', 'shipping_cost', 'discount_amount', 'tax_amount', 'total_amount')
    search_fields = ('order__order_id',)
    readonly_fields = tuple(f.name for f in OrderFinancialSnapshot._meta.fields)


@admin.register(OrderItemSnapshot)
class OrderItemSnapshotAdmin(ModelAdmin):
    list_display = ('snapshot_id', 'order_item', 'product_name', 'volume_ml', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('product_name', 'brand_name', 'order_item__order__order_id')
    readonly_fields = tuple(f.name for f in OrderItemSnapshot._meta.fields)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(ModelAdmin):
    list_display = ('history_id', 'order', 'status', 'changed_by', 'created_at')
    search_fields = ('order__order_id', 'changed_by__email', 'note')
    list_filter = ('status', 'created_at')
    readonly_fields = ('history_id', 'created_at')


@admin.register(ReturnRequest)
class ReturnRequestAdmin(ModelAdmin):
    list_display = ('return_id', 'order', 'customer', 'reason', 'status_badge', 'refund_amount', 'requested_at')
    list_display_links = ('return_id', 'order')
    search_fields = ('order__order_id', 'order__user__email', 'order__user__first_name', 'order__user__last_name', 'reason', 'details')
    list_filter = ('status', 'reason', 'requested_at')
    readonly_fields = ('return_id', 'requested_at', 'reviewed_at', 'updated_at')
    fieldsets = (
        ('Return Request', {'fields': ('return_id', 'order', 'reason', 'details', 'status', 'refund_amount')}),
        ('Admin Review', {'fields': ('admin_note', 'requested_at', 'reviewed_at', 'updated_at')}),
    )

    @admin.display(description='Customer')
    def customer(self, obj):
        return obj.order.user.email

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return obj.status

    def save_model(self, request, obj, form, change):
        if obj.status in (ReturnStatus.APPROVED, ReturnStatus.REJECTED, ReturnStatus.RECEIVED, ReturnStatus.REFUNDED) and not obj.reviewed_at:
            obj.reviewed_at = timezone.now()
        if obj.status == ReturnStatus.REFUNDED and obj.refund_amount <= 0:
            obj.refund_amount = obj.order.total_amount
        super().save_model(request, obj, form, change)
        if obj.status == ReturnStatus.REFUNDED:
            from accounts.models import Payment, Invoice
            Payment.objects.filter(order=obj.order).update(status='Refunded')
            Invoice.objects.filter(order=obj.order).update(status='Refunded')
