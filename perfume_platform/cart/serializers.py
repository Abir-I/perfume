from decimal import Decimal

from rest_framework import serializers

from accounts.models import Cart, CartItem, Product


class ProductMiniSerializer(serializers.ModelSerializer):
    """Just enough product info for a cart line item."""
    perfume_name = serializers.CharField(source='perfume.perfume_name', read_only=True)
    brand_name = serializers.CharField(source='perfume.brand.brand_name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'product_id', 'perfume_name', 'brand_name',
            'product_type', 'volume_ml', 'price', 'stock_quantity',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['cart_item_id', 'product', 'quantity', 'added_at', 'subtotal']

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price


class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['cart_id', 'created_at', 'updated_at', 'items', 'total']

    def get_items(self, obj):
        items = obj.cartitem_set.select_related('product__perfume__brand').order_by('added_at')
        return CartItemSerializer(items, many=True).data

    def get_total(self, obj):
        items = obj.cartitem_set.select_related('product')
        return sum((item.quantity * item.product.price for item in items), Decimal('0.00'))


class AddCartItemSerializer(serializers.Serializer):
    """
    Input for adding a product to the cart.

    Quantity must be a positive whole number - zero, negative, or
    non-integer values (e.g. "abc", 2.5) are all rejected before anything
    touches the database.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Quantity must be a positive whole number greater than zero.'
            )
        return value

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(product_id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError('This product does not exist.')

        if not product.is_active:
            raise serializers.ValidationError('This product is not currently available.')

        # stash the resolved product so the view doesn't have to re-query it
        self._product = product
        return value

    def get_product(self):
        return self._product
