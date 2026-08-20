from rest_framework import serializers
from .models import Perfume, Brand, Product, BulkBottle

def normalize_image_url(value):
    """Convert legacy image references into browser-safe public URLs.

    The database historically stored a mix of absolute URLs, /media/... URLs,
    media/... paths, and perfumes/... relative storage paths.  Keep external
    URLs untouched and consistently expose local uploads under MEDIA_URL.
    """
    if not value:
        return ''
    value = str(value).strip().replace('\\', '/')
    if not value:
        return ''

    # Fully qualified remote/data URLs.
    if value.startswith(('http://', 'https://', 'data:')):
        return value

    # Absolute local filesystem paths from older records:
    # C:/.../media/perfumes/foo.jpg -> /media/perfumes/foo.jpg
    media_marker = '/media/'
    lower = value.lower()
    marker_index = lower.find(media_marker)
    if marker_index >= 0:
        return '/media/' + value[marker_index + len(media_marker):].lstrip('/')

    value = value.lstrip('/')
    if value.startswith('media/'):
        return '/' + value
    if value.startswith('static/'):
        return '/' + value
    if value.startswith('perfumes/'):
        return '/media/' + value
    # Bare legacy filenames were uploaded into the perfumes directory.
    if '/' not in value:
        return '/media/perfumes/' + value

    # Preserve other explicitly-rooted application URLs.
    return '/' + value


# ✅ FIXED: Serializers now properly handle image_url from database

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['brand_id', 'brand_name', 'country_of_origin', 'description']


class PerfumeSerializer(serializers.ModelSerializer):
    """✅ FIXED: Properly handle image_url from database"""
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    
    # ✅ FIXED: Use SerializerMethodField to properly return image_url
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        return normalize_image_url(obj.image_url)
    
    class Meta:
        model = Perfume
        fields = [
            'perfume_id',
            'perfume_name',
            'brand_id',
            'brand_name',
            'concentration',
            'top_notes',
            'middle_notes',
            'base_notes',
            'longevity_hours',
            'sillage',
            'recommended_season',
            'target_gender',
            'description',
            'image_url',  # ✅ Now correctly mapped from database
            'created_at',
        ]


class ProductSerializer(serializers.ModelSerializer):
    """✅ FIXED: Get image_url from related Perfume model"""
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    brand_name = serializers.CharField(source='perfume.brand.brand_name', read_only=True)
    brand_id = serializers.IntegerField(source='perfume.brand_id', read_only=True)
    concentration = serializers.CharField(source='perfume.concentration', read_only=True)
    top_notes = serializers.CharField(source='perfume.top_notes', read_only=True)
    middle_notes = serializers.CharField(source='perfume.middle_notes', read_only=True)
    base_notes = serializers.CharField(source='perfume.base_notes', read_only=True)
    longevity_hours = serializers.DecimalField(
        source='perfume.longevity_hours', 
        max_digits=4, 
        decimal_places=1, 
        read_only=True
    )
    sillage = serializers.CharField(source='perfume.sillage', read_only=True)
    
    # ✅ FIXED: Get image_url from perfume model
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        return normalize_image_url(obj.perfume.image_url if obj.perfume else '')
    
    target_gender = serializers.CharField(source='perfume.target_gender', read_only=True)
    recommended_season = serializers.CharField(source='perfume.recommended_season', read_only=True)

    class Meta:
        model = Product
        fields = [
            'product_id',
            'perfume_id',
            'perfume_name',
            'brand_id',
            'brand_name',
            'concentration',
            'top_notes',
            'middle_notes',
            'base_notes',
            'longevity_hours',
            'sillage',
            'volume_ml',
            'price',
            'stock_quantity',
            'product_type',
            'image_url',  # ✅ Now correctly mapped
            'target_gender',
            'recommended_season',
        ]


class BulkBottleSerializer(serializers.ModelSerializer):
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        return normalize_image_url(obj.perfume.image_url if obj.perfume else '')
    
    class Meta:
        model = BulkBottle
        fields = [
            'bottle_id',
            'perfume_id',
            'perfume_name',
            'batch_number',
            'purchase_date',
            'bottle_size_ml',
            'ml_remaining',
            'cost_price',
            'supplier_name',
            'authenticity_verified',
            'image_url',
        ]
