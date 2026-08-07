"""Cart API - uses the project's real accounts.User + cart/cart_item tables."""

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem
from catalog.models import Product


class BaseCartView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_user(self, request):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False) or not hasattr(user, 'user_id'):
            return None
        return user

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(
            user_id=user.user_id,
            defaults={
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
            },
        )
        return cart

    def item_payload(self, item):
        product = item.product
        perfume = product.perfume
        brand = perfume.brand
        final_price = getattr(perfume, 'final_price', None) or product.price
        image = getattr(perfume, 'image_url', None) or getattr(perfume, 'image', None)
        image = str(image) if image else None
        if image and not image.startswith(('http://', 'https://', '/')):
            image = '/media/' + image

        return {
            'id': item.cart_item_id,
            'cart_item_id': item.cart_item_id,
            'product_id': product.product_id,
            'product_name': perfume.perfume_name,
            'perfume_name': perfume.perfume_name,
            'brand': brand.brand_name,
            'brand_name': brand.brand_name,
            'price': float(product.price),
            'final_price': float(final_price),
            'quantity': item.quantity,
            'stock_quantity': int(product.stock_quantity or 0),
            'image': image,
            'image_url': image,
            'subtotal': round(float(final_price) * item.quantity, 2),
        }

    def cart_payload(self, cart, message='Cart loaded'):
        items = list(
            CartItem.objects.select_related(
                'product', 'product__perfume', 'product__perfume__brand'
            ).filter(cart=cart).order_by('added_at')
        )
        payload_items = [self.item_payload(item) for item in items]
        subtotal = round(sum(item['subtotal'] for item in payload_items), 2)
        shipping = 0
        tax = 0
        total = round(subtotal + shipping + tax, 2)
        total_items = sum(item['quantity'] for item in payload_items)

        return {
            'message': message,
            'storage': 'database',
            'cart_id': cart.cart_id,
            'items': payload_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'total_price': total,
            'total': total,
            'total_items': total_items,
        }


class CartListView(BaseCartView):
    """GET /api/cart/"""

    def get(self, request):
        user = self.get_user(request)
        if not user:
            return Response({'error': 'Please log in to view your cart.'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(self.cart_payload(self.get_cart(user)))


class AddToCartView(BaseCartView):
    """POST /api/cart/add/ {product_id, quantity}"""

    def post(self, request):
        user = self.get_user(request)
        if not user:
            return Response({'error': 'Please log in to add items to your cart.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            product_id = int(request.data.get('product_id'))
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid product or quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'Quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.select_related('perfume', 'perfume__brand').get(product_id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not product.is_active:
            return Response({'error': 'This product is not currently available.'}, status=status.HTTP_400_BAD_REQUEST)

        stock = int(product.stock_quantity or 0)
        if stock <= 0:
            return Response({'error': 'This item is out of stock.'}, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_cart(user)
        with transaction.atomic():
            item = CartItem.objects.filter(cart=cart, product=product).first()
            new_quantity = min((item.quantity if item else 0) + quantity, stock)
            if item:
                item.quantity = new_quantity
                item.save(update_fields=['quantity'])
            else:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=min(quantity, stock),
                    added_at=timezone.now(),
                )
            Cart.objects.filter(pk=cart.cart_id).update(updated_at=timezone.now())

        return Response(
            self.cart_payload(cart, 'Added to cart'),
            status=status.HTTP_201_CREATED,
        )


class UpdateCartItemView(BaseCartView):
    """PATCH /api/cart/items/<cart_item_id>/update/"""

    def patch(self, request, item_id):
        user = self.get_user(request)
        if not user:
            return Response({'error': 'Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            quantity = int(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = CartItem.objects.select_related('product').get(
                cart__user_id=user.user_id,
                cart_item_id=item_id,
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
        else:
            stock = int(item.product.stock_quantity or 0)
            if stock <= 0:
                return Response({'error': 'This item is out of stock.'}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = min(quantity, stock)
            item.save(update_fields=['quantity'])

        cart = self.get_cart(user)
        Cart.objects.filter(pk=cart.cart_id).update(updated_at=timezone.now())
        return Response(self.cart_payload(cart, 'Cart updated'))


class RemoveFromCartView(BaseCartView):
    """DELETE /api/cart/items/<cart_item_id>/remove/"""

    def delete(self, request, item_id):
        user = self.get_user(request)
        if not user:
            return Response({'error': 'Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            item = CartItem.objects.get(
                cart__user_id=user.user_id,
                cart_item_id=item_id,
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart = item.cart
        item.delete()
        Cart.objects.filter(pk=cart.cart_id).update(updated_at=timezone.now())
        return Response(self.cart_payload(cart, 'Item removed from cart'))


class ClearCartView(BaseCartView):
    """DELETE /api/cart/clear/"""

    def delete(self, request):
        user = self.get_user(request)
        if not user:
            return Response({'error': 'Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)
        cart = self.get_cart(user)
        CartItem.objects.filter(cart=cart).delete()
        Cart.objects.filter(pk=cart.cart_id).update(updated_at=timezone.now())
        return Response(self.cart_payload(cart, 'Cart cleared'))
