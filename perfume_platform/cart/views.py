"""Canonical authenticated cart API.

This API intentionally uses the same unmanaged cart tables/models as the
storefront (accounts.models.Cart / CartItem).  The previous project had a
second cart implementation in cart.models which uses Django's built-in User;
that caused items added by the storefront to be invisible to the cart sidebar.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem, Product


class CanonicalCartMixin:
    authentication_classes = [CustomJWTAuthentication]

    def get_user(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False) and hasattr(user, 'user_id'):
            return user
        return None

    def get_cart(self, request):
        user = self.get_user(request)
        if user is None:
            return None
        cart, _ = Cart.objects.get_or_create(
            user_id=user.user_id,
            defaults={
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
            },
        )
        return cart

    @staticmethod
    def serialize_item(item):
        product = item.product
        perfume = product.perfume
        brand = perfume.brand
        image = (perfume.image_url or '').strip() if perfume.image_url else ''
        return {
            'id': item.cart_item_id,
            'cart_item_id': item.cart_item_id,
            'product_id': product.product_id,
            'product_name': perfume.perfume_name,
            'brand': brand.brand_name,
            'product_type': product.product_type,
            'volume_ml': float(product.volume_ml) if product.volume_ml is not None else None,
            'price': float(product.price),
            'final_price': float(product.price),
            'quantity': int(item.quantity),
            'image': image or None,
            'image_url': image or None,
            'subtotal': round(float(product.price) * int(item.quantity), 2),
        }

    def serialize_cart(self, cart, message='Cart loaded'):
        items = list(
            CartItem.objects.select_related('product', 'product__perfume', 'product__perfume__brand')
            .filter(cart=cart)
            .order_by('added_at')
        )
        payload = [self.serialize_item(item) for item in items]
        total = sum(item['subtotal'] for item in payload)
        count = sum(item['quantity'] for item in payload)
        return {
            'message': message,
            'cart_id': cart.cart_id,
            'items': payload,
            'subtotal': round(total, 2),
            'shipping': 0,
            'tax': 0,
            'total_price': round(total, 2),
            'total_items': count,
        }


class CartListView(CanonicalCartMixin, APIView):
    """GET /api/cart/"""

    def get(self, request):
        cart = self.get_cart(request)
        if cart is None:
            return Response({'items': [], 'subtotal': 0, 'shipping': 0, 'tax': 0,
                             'total_price': 0, 'total_items': 0}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(self.serialize_cart(cart))


class AddToCartView(CanonicalCartMixin, APIView):
    """POST /api/cart/add/ {product_id, quantity}"""

    def post(self, request):
        user = self.get_user(request)
        if user is None:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            product_id = int(request.data.get('product_id'))
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid product or quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'Quantity must be positive.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.select_related('perfume', 'perfume__brand').get(product_id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not product.is_active:
            return Response({'error': 'Product is not available.'}, status=status.HTTP_400_BAD_REQUEST)

        if product.stock_quantity < quantity:
            return Response({'error': f'Insufficient stock. Available: {product.stock_quantity}.'},
                            status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_cart(request)
        item = CartItem.objects.filter(cart=cart, product=product).first()
        if item:
            new_quantity = item.quantity + quantity
            if new_quantity > product.stock_quantity:
                return Response({'error': f'Cannot add more. Available stock: {product.stock_quantity}.'},
                                status=status.HTTP_400_BAD_REQUEST)
            item.quantity = new_quantity
            item.save(update_fields=['quantity'])
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity, added_at=timezone.now())

        Cart.objects.filter(pk=cart.pk).update(updated_at=timezone.now())
        return Response(self.serialize_cart(cart, 'Item added to cart'), status=status.HTTP_201_CREATED)


class UpdateCartItemView(CanonicalCartMixin, APIView):
    """PATCH /api/cart/items/<item_id>/update/"""

    def patch(self, request, item_id):
        cart = self.get_cart(request)
        if cart is None:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = CartItem.objects.get(cart=cart, cart_item_id=item_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
            message = 'Item removed from cart'
        else:
            if quantity > item.product.stock_quantity:
                return Response({'error': f'Only {item.product.stock_quantity} available.'},
                                status=status.HTTP_400_BAD_REQUEST)
            item.quantity = quantity
            item.save(update_fields=['quantity'])
            message = 'Quantity updated'

        return Response(self.serialize_cart(cart, message))


class RemoveFromCartView(CanonicalCartMixin, APIView):
    """DELETE /api/cart/items/<item_id>/remove/"""

    def delete(self, request, item_id):
        cart = self.get_cart(request)
        if cart is None:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        deleted, _ = CartItem.objects.filter(cart=cart, cart_item_id=item_id).delete()
        if not deleted:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serialize_cart(cart, 'Item removed from cart'))


class ClearCartView(CanonicalCartMixin, APIView):
    """DELETE /api/cart/clear/"""

    def delete(self, request):
        cart = self.get_cart(request)
        if cart is None:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        CartItem.objects.filter(cart=cart).delete()
        return Response(self.serialize_cart(cart, 'Cart cleared'))
