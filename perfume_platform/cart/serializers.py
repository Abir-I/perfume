from decimal import Decimal

from django.db.models import Sum
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
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['cart_item_id', 'product', 'quantity', 'added_at', 'line_total']

    def get_line_total(self, obj):
        return obj.quantity * obj.product.price


class CartSerializer(serializers.ModelSerializer):
    """
    Full cart representation used by GET /api/cart/, and returned by every
    cart-mutating endpoint (add/remove/update) so the UI can re-render from
    a single response instead of making a second request.
    """
    items = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['cart_id', 'created_at', 'updated_at', 'items', 'item_count', 'subtotal', 'total']

    def _items_qs(self, obj):
        return obj.cartitem_set.select_related('product__perfume__brand').order_by('added_at')

    def get_items(self, obj):
        return CartItemSerializer(self._items_qs(obj), many=True).data

    def get_item_count(self, obj):
        # total number of units across all lines (2x perfume A + 1x perfume B = 3)
        return self._items_qs(obj).aggregate(total=Sum('quantity'))['total'] or 0

    def get_subtotal(self, obj):
        items = self._items_qs(obj)
        return sum((item.quantity * item.product.price for item in items), Decimal('0.00'))

    def get_total(self, obj):
        # No tax/shipping is applied at the cart stage - those are only
        # calculated at checkout (see orders/views.py). At the cart stage
        # total == subtotal; kept as a separate field so the cart-page UI
        # doesn't need special-casing versus the checkout response.
        return self.get_subtotal(obj)


class AddCartItemSerializer(serializers.Serializer):
    """
    Input for POST /api/cart/add/.

    Quantity must be a positive whole number - zero, negative, or
    non-integer values (e.g. "abc", 2.5) are all rejected before anything
    touches the database.

    `volume` is optional. Each Product row already represents one specific
    volume/variant (see Product.volume_ml), so product_id alone is enough
    to add the right item - `volume` is accepted purely as a safety check
    for the UI (e.g. the customer picked "50ml" in a dropdown): if it's
    sent and doesn't match the chosen product's actual volume, the request
    is rejected instead of silently adding the wrong variant.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)
    volume = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

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

    def validate(self, data):
        product = getattr(self, '_product', None)
        volume = data.get('volume')
        if product is not None and volume is not None and product.volume_ml != volume:
            raise serializers.ValidationError({
                'volume': (
                    f"This product is sold in {product.volume_ml}ml, not {volume}ml. "
                    f"Use the product_id for the {volume}ml variant instead."
                )
            })
        return data

    def get_product(self):
        return self._product


class UpdateCartItemSerializer(serializers.Serializer):
    """Input for PATCH /api/cart/update/{cart_item_id}/."""
    quantity = serializers.IntegerField()

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Quantity must be at least 1. To remove the item entirely, use DELETE /api/cart/remove/{cart_item_id}/ instead.'
            )
        return value
