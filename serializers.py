from rest_framework import serializers

# Brand / Perfume / Product live in accounts/models.py in this project,
# so we import from there instead of redefining them (redefining would
# create a second Model class mapped to the same MySQL table).
from accounts.models import Brand, Product


class BrandListSerializer(serializers.ModelSerializer):
    """Brand List Feature — full list of brands, for filters/menus."""

    class Meta:
        model = Brand
        fields = ['brand_id', 'brand_name', 'country_of_origin']


class ProductListSerializer(serializers.ModelSerializer):
    """
    Product Browsing Feature — one row per product (a specific bottle
    size/type of a perfume), with just enough info for a listing card.
    """
    perfume_id = serializers.IntegerField(source='perfume.perfume_id', read_only=True)
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    brand_id = serializers.IntegerField(source='perfume.brand.brand_id', read_only=True)
    brand_name = serializers.CharField(source='perfume.brand.brand_name', read_only=True)
    image_url = serializers.CharField(source='perfume.image_url', read_only=True)

    class Meta:
        model = Product
        fields = [
            'product_id',
            'perfume_id',
            'perfume_name',
            'brand_id',
            'brand_name',
            'product_type',
            'volume_ml',
            'price',
            'stock_quantity',
            'image_url',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Single Product Page Feature — everything about one product in a
    single response: brand, notes, price, and the rest of the perfume
    detail, so the frontend only needs one request per page.
    """
    perfume_id = serializers.IntegerField(source='perfume.perfume_id', read_only=True)
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    brand_id = serializers.IntegerField(source='perfume.brand.brand_id', read_only=True)
    brand_name = serializers.CharField(source='perfume.brand.brand_name', read_only=True)
    concentration = serializers.CharField(source='perfume.concentration', read_only=True)
    top_notes = serializers.CharField(source='perfume.top_notes', read_only=True)
    middle_notes = serializers.CharField(source='perfume.middle_notes', read_only=True)
    base_notes = serializers.CharField(source='perfume.base_notes', read_only=True)
    longevity_hours = serializers.DecimalField(
        source='perfume.longevity_hours', max_digits=4, decimal_places=1, read_only=True
    )
    sillage = serializers.CharField(source='perfume.sillage', read_only=True)
    recommended_season = serializers.CharField(source='perfume.recommended_season', read_only=True)
    target_gender = serializers.CharField(source='perfume.target_gender', read_only=True)
    description = serializers.CharField(source='perfume.description', read_only=True)
    image_url = serializers.CharField(source='perfume.image_url', read_only=True)

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
            'recommended_season',
            'target_gender',
            'description',
            'image_url',
            'product_type',
            'volume_ml',
            'price',
            'stock_quantity',
        ]
