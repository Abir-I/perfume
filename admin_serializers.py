from django.db.models import Sum
from rest_framework import serializers

from accounts.models import Perfume, Product


class PerfumeAdminSerializer(serializers.ModelSerializer):
    """
    Admin Panel Backend — used to create and edit perfumes from the
    admin dashboard (Abir's admin forms POST/PUT here).
    """

    class Meta:
        model = Perfume
        fields = [
            'perfume_id',
            'brand',
            'perfume_name',
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
        ]
        read_only_fields = ['perfume_id', 'image_url']  


class ProductVariantAdminSerializer(serializers.ModelSerializer):
    """
    Admin Panel Backend — used to create and edit product variants
    (a specific bottle size/type + price/stock for a perfume).
    """

    class Meta:
        model = Product
        fields = [
            'product_id',
            'perfume',
            'product_type',
            'volume_ml',
            'price',
            'stock_quantity',
            'is_active',
        ]
        read_only_fields = ['product_id', 'perfume']
        extra_kwargs = {
            'is_active': {'required': False},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_volume_ml(self, value):
        if value <= 0:
            raise serializers.ValidationError("Volume must be greater than 0.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity can't be negative.")
        return value


class ProductImageUploadSerializer(serializers.Serializer):
    """Admin Image Upload — validates the file before it touches disk."""

    image = serializers.ImageField()

    ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png')
    MAX_SIZE_BYTES = 5 * 1024 * 1024  

    def validate_image(self, value):
        content_type = getattr(value, 'content_type', '')
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Only JPG and PNG images are allowed.")
        if value.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError("Image must be 5MB or smaller.")
        return value


class AdminSearchResultSerializer(serializers.ModelSerializer):
    """
    Admin Product Search — one row per perfume, with brand name and
    total stock across all its variants, for the admin dashboard
    search bar.
    """
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    current_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Perfume
        fields = ['perfume_id', 'perfume_name', 'brand_name', 'concentration', 'current_stock']
