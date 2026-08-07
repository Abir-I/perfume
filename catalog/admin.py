"""
Catalog Admin Interface
"""

from django.contrib import admin
from .models import Brand, Perfume, Product, Review


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Brand admin"""
    list_display = ('brand_id', 'brand_name', 'country', 'established_year')
    search_fields = ('brand_name', 'country')
    list_filter = ('country', 'established_year')
    fieldsets = (
        ('Basic Info', {
            'fields': ('brand_name', 'description', 'logo')
        }),
        ('Details', {
            'fields': ('country', 'established_year', 'website')
        }),
    )


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    """Perfume admin"""
    list_display = ('perfume_id', 'perfume_name', 'brand', 'concentration', 'final_price', 'stock_status', 'is_featured')
    search_fields = ('perfume_name', 'brand__brand_name')
    list_filter = ('concentration', 'gender', 'season', 'stock_status', 'is_featured', 'is_hot_deal')
    
    fieldsets = (
        ('Basic', {
            'fields': ('perfume_name', 'brand', 'description', 'image')
        }),
        ('Type', {
            'fields': ('concentration', 'size', 'gender', 'season')
        }),
        ('Pricing', {
            'fields': ('base_price', 'discount_type', 'discount_value', 'discount_start', 'discount_end', 'final_price', 'cost_price')
        }),
        ('Limited Edition', {
            'fields': ('is_limited_edition', 'limited_quantity', 'limited_sold')
        }),
        ('Marketing', {
            'fields': ('is_featured', 'is_hot_deal', 'offer_description', 'offer_end_date')
        }),
        ('Stock', {
            'fields': ('stock_status', 'low_stock_threshold', 'allow_backorder', 'warehouse')
        }),
        ('Tags', {
            'fields': ('tags', 'category', 'sub_category')
        }),
    )
    
    readonly_fields = ('final_price',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin"""
    list_display = ('product_id', 'perfume', 'sku', 'price', 'quantity', 'product_type', 'is_active')
    search_fields = ('perfume__perfume_name', 'sku')
    list_filter = ('product_type', 'is_active')
    fieldsets = (
        ('Basic', {
            'fields': ('perfume', 'sku', 'product_type')
        }),
        ('Inventory', {
            'fields': ('price', 'quantity')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Review admin"""
    list_display = ('review_id', 'perfume', 'user_name', 'rating', 'created_at', 'helpful_count')
    search_fields = ('perfume__perfume_name', 'user_name', 'email')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
