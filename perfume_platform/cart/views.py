from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem, Product

from .serializers import AddCartItemSerializer, CartSerializer, UpdateCartItemSerializer


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
    """
    POST /api/cart/add/ - add a product to the logged-in customer's cart.

    Body: {"product_id": 5, "quantity": 2, "volume": 50}   ("volume" optional)

    Validates the product exists, is active, and that enough stock is
    available (existing quantity already in the cart + the amount being
    added, checked against a row-locked read of current stock). Returns
    the full updated cart (items, item_count, subtotal, total).
    """
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
            # Lock the product row for the rest of this transaction so a
            # second "add to cart" for the same product can't both read
            # the same stale stock_quantity at once.
            locked_product = Product.objects.select_for_update().get(product_id=product.product_id)

            existing_item = CartItem.objects.filter(cart=cart, product=locked_product).first()
            already_in_cart = existing_item.quantity if existing_item else 0
            requested_total = already_in_cart + quantity

            if requested_total > locked_product.stock_quantity:
                return Response(
                    {
                        "error": "Not enough stock available for that quantity.",
                        "available": locked_product.stock_quantity,
                        "already_in_cart": already_in_cart,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if existing_item:
                existing_item.quantity = requested_total
                existing_item.save(update_fields=['quantity'])
                created = False
            else:
                CartItem.objects.create(
                    cart=cart, product=locked_product,
                    quantity=quantity, added_at=timezone.now(),
                )
                created = True

            cart.updated_at = timezone.now()
            cart.save(update_fields=['updated_at'])

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(CartSerializer(cart).data, status=response_status)


class CartItemDetailView(APIView):
    """
    PATCH  /api/cart/update/{cart_item_id}/ - change a line's quantity (min 1, max = stock)
    DELETE /api/cart/remove/{cart_item_id}/ - remove a line entirely

    Both return the full updated cart. A cart_item_id that doesn't exist,
    or belongs to someone else's cart, is reported as 404 - never 403 -
    so this never confirms/denies the existence of another user's cart item.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_owned_item(self, request, cart_item_id):
        return CartItem.objects.select_related('cart', 'product').get(
            cart_item_id=cart_item_id, cart__user=request.user,
        )

    def patch(self, request, cart_item_id):
        try:
            item = self._get_owned_item(request, cart_item_id)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        quantity = serializer.validated_data['quantity']

        with transaction.atomic():
            locked_product = Product.objects.select_for_update().get(product_id=item.product_id)

            if quantity > locked_product.stock_quantity:
                return Response(
                    {
                        "error": "Not enough stock available for that quantity.",
                        "available": locked_product.stock_quantity,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item.quantity = quantity
            item.save(update_fields=['quantity'])
            item.cart.updated_at = timezone.now()
            item.cart.save(update_fields=['updated_at'])

        return Response(CartSerializer(item.cart).data, status=status.HTTP_200_OK)

    def delete(self, request, cart_item_id):
        try:
            item = self._get_owned_item(request, cart_item_id)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        cart = item.cart
        item.delete()
        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
