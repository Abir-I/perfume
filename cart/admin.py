"""
Cart Admin Interface
"""

from django.contrib import admin
from .models import Cart, CartItem, Coupon


class CartItemInline(admin.TabularInline):
    """Inline cart items"""
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)
    fields = ('product', 'quantity', 'added_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Cart admin"""
    list_display = ('id', 'user', 'session_key', 'created_at', 'items_count', 'total_price')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'
    
    def total_price(self, obj):
        return f"${obj.get_total_price():.2f}"
    total_price.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Cart item admin"""
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal', 'added_at')
    search_fields = ('product__perfume__perfume_name', 'cart__user__username')
    readonly_fields = ('added_at',)
    
    def subtotal(self, obj):
        return f"${obj.get_subtotal():.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Coupon admin"""
    list_display = ('code', 'discount_percentage', 'discount_amount', 'is_active', 'times_used', 'usage_limit')
    search_fields = ('code',)
    list_filter = ('is_active', 'valid_from', 'valid_until')
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'is_active')
        }),
        ('Discount', {
            'fields': ('discount_percentage', 'discount_amount')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Usage', {
            'fields': ('usage_limit', 'times_used')
        }),
    )
