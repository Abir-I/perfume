from rest_framework import serializers

from accounts.models import Address, CustomerOrder, OrderItem


class CheckoutSerializer(serializers.Serializer):
    """Input for POST /api/orders/checkout/."""
    address_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'address_id', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """One line of an order, with enough product info for an order-detail page."""
    product_id = serializers.IntegerField(source='product.product_id', read_only=True)
    perfume_name = serializers.CharField(source='product.perfume.perfume_name', read_only=True)
    brand_name = serializers.CharField(source='product.perfume.brand.brand_name', read_only=True)
    volume_ml = serializers.DecimalField(source='product.volume_ml', max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'order_item_id', 'product_id', 'perfume_name', 'brand_name',
            'volume_ml', 'quantity', 'unit_price', 'subtotal',
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order detail for GET /api/orders/{order_id}/."""
    address = AddressSerializer(read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = CustomerOrder
        fields = ['order_id', 'status', 'order_date', 'total_amount', 'notes', 'address', 'items']

    def get_items(self, obj):
        items = obj.orderitem_set.select_related('product__perfume__brand').order_by('order_item_id')
        return OrderItemSerializer(items, many=True).data


class OrderListItemSerializer(serializers.ModelSerializer):
    """One row of GET /api/orders/ (order list) - summary only, no line items."""

    class Meta:
        model = CustomerOrder
        fields = ['order_id', 'status', 'order_date', 'total_amount']
