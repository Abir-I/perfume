from rest_framework import serializers


class CheckoutSerializer(serializers.Serializer):
    """Input for POST /api/orders/checkout/."""
    address_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
