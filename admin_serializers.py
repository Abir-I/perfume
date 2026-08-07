from rest_framework import serializers

from accounts.models import Brand


class PerfumeWriteSerializer(serializers.Serializer):
    """Input for creating or editing a perfume from the admin panel."""

    brand_id = serializers.IntegerField()
    perfume_name = serializers.CharField(max_length=200)
    concentration = serializers.CharField(max_length=7)
    top_notes = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    middle_notes = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    base_notes = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    longevity_hours = serializers.DecimalField(
        max_digits=4, decimal_places=1, required=False, allow_null=True, default=None
    )
    sillage = serializers.CharField(max_length=8, required=False, allow_blank=True, default='')
    recommended_season = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    target_gender = serializers.CharField(max_length=6)
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_perfume_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Perfume name can't be blank.")
        return value

    def validate_brand_id(self, value):
        try:
            brand = Brand.objects.get(brand_id=value)
        except Brand.DoesNotExist:
            raise serializers.ValidationError("This brand does not exist.")
        self._brand = brand
        return value

    def get_brand(self):
        return self._brand


class ProductVariantWriteSerializer(serializers.Serializer):
    """Input for creating or editing a product variant (size/price/stock)."""

    product_type = serializers.CharField(max_length=11)
    volume_ml = serializers.DecimalField(max_digits=8, decimal_places=2)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = serializers.IntegerField()
    is_active = serializers.BooleanField(default=True)

    def validate_product_type(self, value):
        if not value.strip():
            raise serializers.ValidationError("Product type can't be blank.")
        return value

    def validate_volume_ml(self, value):
        if value <= 0:
            raise serializers.ValidationError("Volume must be greater than 0.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity can't be negative.")
        return value


class ProductImageUploadSerializer(serializers.Serializer):
    """Validates an uploaded product image before it touches disk."""

    image = serializers.ImageField()

    ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png')
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

    def validate_image(self, value):
        content_type = getattr(value, 'content_type', '')
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Only JPG and PNG images are allowed.")
        if value.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError("Image must be 5MB or smaller.")
        return value
