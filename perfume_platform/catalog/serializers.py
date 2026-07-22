from rest_framework import serializers
from accounts.models import Brand, Perfume, Product


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['brand_id', 'brand_name']


class PerfumeSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    
    class Meta:
        model = Perfume
        fields = [
            'perfume_id',
            'brand_id',
            'brand_name',
            'perfume_name',
            'concentration',
            'longevity_hours',
            'top_notes',
            'middle_notes',
            'base_notes',
            'recommended_season',
            'target_gender',
            'image_url',
        ]


class ProductSerializer(serializers.ModelSerializer):
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    brand_name = serializers.CharField(source='perfume.brand.brand_name', read_only=True)
    concentration = serializers.CharField(source='perfume.concentration', read_only=True)
    top_notes = serializers.CharField(source='perfume.top_notes', read_only=True)
    middle_notes = serializers.CharField(source='perfume.middle_notes', read_only=True)
    base_notes = serializers.CharField(source='perfume.base_notes', read_only=True)
    image_url = serializers.CharField(source='perfume.image_url', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'product_id',
            'perfume_id',
            'perfume_name',
            'brand_name',
            'concentration',
            'top_notes',
            'middle_notes',
            'base_notes',
            'volume_ml',
            'price',
            'stock_quantity',
            'product_type',
            'image_url',
        ]