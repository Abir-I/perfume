from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem

from .serializers import AddCartItemSerializer, CartSerializer


def _get_or_create_cart(user):
    """Every customer gets exactly one cart (cart table has a UNIQUE user_id)."""
    now = timezone.now()
    cart, _ = Cart.objects.get_or_create(
        user=user,
        defaults={'created_at': now, 'updated_at': now},
    )
    return cart


class CartView(APIView):
    """GET /api/cart/ - view the logged-in customer's cart and its items."""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class AddCartItemView(APIView):
    """POST /api/cart/items/ - add a product to the logged-in customer's cart."""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.get_product()
        quantity = serializer.validated_data['quantity']
        cart = _get_or_create_cart(request.user)

        with transaction.atomic():
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity, 'added_at': timezone.now()},
            )
            if not created:
                # already in the cart - top up the quantity instead of
                # erroring out on the unique (cart, product) constraint
                item.quantity += quantity
                item.save(update_fields=['quantity'])

            cart.updated_at = timezone.now()
            cart.save(update_fields=['updated_at'])

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(CartSerializer(cart).data, status=response_status)
