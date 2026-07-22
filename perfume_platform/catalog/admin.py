from django.contrib import admin
from accounts.models import Brand, Perfume, Product, BulkBottle, DecantBatch


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['brand_id', 'brand_name']
    search_fields = ['brand_name']


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ['perfume_id', 'perfume_name', 'brand', 'longevity_hours']
    search_fields = ['perfume_name', 'brand__brand_name', 'top_notes', 'base_notes']
    list_filter = ['brand', 'target_gender', 'recommended_season']
    readonly_fields = ['perfume_id', 'created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'perfume', 'volume_ml', 'price', 'stock_quantity']
    search_fields = ['perfume__perfume_name', 'perfume__brand__brand_name']
    list_filter = ['product_type', 'is_active']
    readonly_fields = ['product_id', 'created_at']
    fieldsets = (
        ('Product Info', {
            'fields': ('product_id', 'perfume', 'product_type', 'volume_ml')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BulkBottle)
class BulkBottleAdmin(admin.ModelAdmin):
    list_display = ['bottle_id', 'perfume', 'batch_number', 'ml_remaining', 'authenticity_verified']
    search_fields = ['perfume__perfume_name', 'batch_number']
    list_filter = ['authenticity_verified', 'purchase_date']
    readonly_fields = ['bottle_id']
    fieldsets = (
        ('Bottle Info', {
            'fields': ('bottle_id', 'perfume', 'batch_number', 'purchase_date')
        }),
        ('Stock', {
            'fields': ('bottle_size_ml', 'ml_remaining')
        }),
        ('Pricing & Supplier', {
            'fields': ('cost_price', 'supplier_name')
        }),
        ('Authenticity', {
            'fields': ('authenticity_verified', 'verification_notes')
        }),
    )


@admin.register(DecantBatch)
class DecantBatchAdmin(admin.ModelAdmin):
    list_display = ['decant_batch_id', 'bottle', 'product', 'quantity_created', 'quantity_sold']
    search_fields = ['bottle__batch_number', 'product__perfume__perfume_name']
    list_filter = ['date_created']
    readonly_fields = ['decant_batch_id', 'date_created']