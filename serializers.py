from rest_framework import serializers

from accounts.models import Product, Review


class ReviewSerializer(serializers.ModelSerializer):
    """Output shape for a single review."""
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'review_id',
            'product_id',
            'user_name',
            'rating',
            'comment',
            'created_at',
            'is_verified_purchase',
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class CreateReviewSerializer(serializers.Serializer):
    """Input for POST /api/reviews/."""

    product_id = serializers.IntegerField()
    rating = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True, max_length=2000, default='')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(product_id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("This product does not exist.")
        self._product = product
        return value

    def get_product(self):
        return self._product
