"""
Product Details page — API endpoints.

Reuses the existing accounts.models (Brand / Perfume / Product / Review)
and the existing `cart` / `cart_item` tables. Nothing here duplicates the
product model or the database schema.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem, Product, Review, OrderItem

from .detail_utils import (
    GUEST_CART_KEY,
    card_payload,
    detail_payload,
    get_product_or_none,
    push_recently_viewed,
    recently_viewed,
    related_products,
    resolve_product,
    review_payload,
    toggle_wishlist,
    wishlist_ids,
    wishlist_products,
)


def _current_user(request):
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False) and hasattr(user, 'user_id'):
        return user
    return None


# ══════════════════════════════════════════════════════════════
#  PRODUCT DETAIL
# ══════════════════════════════════════════════════════════════
class ProductFullDetailView(APIView):
    """GET /api/catalog/products/<product_id>/detail/"""

    authentication_classes = [CustomJWTAuthentication]

    def get(self, request, product_id):
        product = get_product_or_none(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        push_recently_viewed(request, product.product_id)

        reviews = (
            Review.objects.select_related('user')
            .filter(product__perfume=product.perfume)
            .order_by('-created_at')[:20]
        )

        data = detail_payload(product, request)
        data['reviews'] = [review_payload(r) for r in reviews]
        data['related'] = related_products(product)
        data['recently_viewed'] = recently_viewed(request, exclude_id=product.product_id)
        data['in_wishlist'] = product.product_id in wishlist_ids(request)
        return Response(data, status=status.HTTP_200_OK)


class ProductBySlugView(APIView):
    """GET /api/catalog/products/by-slug/<slug>/ — slug based lookup."""

    def get(self, request, slug):
        product = resolve_product(slug=slug)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'product_id': product.product_id, 'url': detail_payload(product)['url']})


class RelatedProductsView(APIView):
    """GET /api/catalog/products/<product_id>/related/"""

    def get(self, request, product_id):
        product = get_product_or_none(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'results': related_products(product)})


# ══════════════════════════════════════════════════════════════
#  REVIEWS
# ══════════════════════════════════════════════════════════════
class ProductReviewsView(APIView):
    """GET / POST  /api/catalog/products/<product_id>/reviews/"""

    authentication_classes = [CustomJWTAuthentication]

    def get(self, request, product_id):
        product = get_product_or_none(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        reviews = (
            Review.objects.select_related('user')
            .filter(product__perfume=product.perfume)
            .order_by('-created_at')
        )
        return Response({
            'count': reviews.count(),
            'summary': detail_payload(product)['rating'],
            'results': [review_payload(r) for r in reviews[:50]],
        })

    def post(self, request, product_id):
        user = _current_user(request)
        if not user:
            return Response(
                {'error': 'Please log in to write a review.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        product = get_product_or_none(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            rating = int(request.data.get('rating', 0))
        except (TypeError, ValueError):
            rating = 0
        if rating < 1 or rating > 5:
            return Response({'error': 'Rating must be between 1 and 5.'},
                            status=status.HTTP_400_BAD_REQUEST)

        comment = (request.data.get('comment') or '').strip()

        verified = OrderItem.objects.filter(
            order__user_id=user.user_id, product_id=product.product_id
        ).exists()
        if not verified:
            return Response(
                {'error': 'You can review only products you have purchased.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        existing = Review.objects.filter(user_id=user.user_id, product_id=product.product_id).first()
        if existing:
            existing.rating = rating
            existing.comment = comment
            existing.is_verified_purchase = 1
            existing.save(update_fields=['rating', 'comment', 'is_verified_purchase'])
            review, created = existing, False
        else:
            review = Review.objects.create(
                user_id=user.user_id,
                product_id=product.product_id,
                rating=rating,
                comment=comment,
                created_at=timezone.now(),
                is_verified_purchase=1,
            )
            created = True
        return Response(
            {
                'message': 'Review published' if created else 'Review updated',
                'review': review_payload(review),
                'summary': detail_payload(product)['rating'],
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ══════════════════════════════════════════════════════════════
#  CART (AJAX) — DB cart for logged-in users, session cart for guests
# ══════════════════════════════════════════════════════════════
def _guest_cart(request):
    return request.session.get(GUEST_CART_KEY, {})


def _save_guest_cart(request, cart):
    request.session[GUEST_CART_KEY] = cart
    request.session.modified = True


def _guest_cart_response(request, message='Cart updated'):
    cart = _guest_cart(request)
    ids = [int(k) for k in cart.keys()]
    products = {
        p.product_id: p
        for p in Product.objects.select_related('perfume', 'perfume__brand').filter(
            product_id__in=ids
        )
    }
    items, total, count = [], 0.0, 0
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if not product:
            continue
        subtotal = float(product.price) * qty
        total += subtotal
        count += qty
        payload = card_payload(product)
        payload.update({'quantity': qty, 'subtotal': round(subtotal, 2)})
        items.append(payload)
    return Response({
        'message': message,
        'storage': 'session',
        'items': items,
        'total_items': count,
        'total_price': round(total, 2),
    })


def _db_cart_response(request, user, message='Cart updated'):
    cart, _ = Cart.objects.get_or_create(
        user_id=user.user_id,
        defaults={'created_at': timezone.now(), 'updated_at': timezone.now()},
    )
    rows = CartItem.objects.select_related(
        'product', 'product__perfume', 'product__perfume__brand'
    ).filter(cart=cart)

    items, total, count = [], 0.0, 0
    for row in rows:
        subtotal = float(row.product.price) * row.quantity
        total += subtotal
        count += row.quantity
        payload = card_payload(row.product)
        payload.update({
            'cart_item_id': row.cart_item_id,
            'quantity': row.quantity,
            'subtotal': round(subtotal, 2),
        })
        items.append(payload)

    return Response({
        'message': message,
        'storage': 'database',
        'cart_id': cart.cart_id,
        'items': items,
        'total_items': count,
        'total_price': round(total, 2),
    })


class StorefrontCartView(APIView):
    """GET /api/catalog/cart/ — current cart (guest or logged-in)."""

    authentication_classes = [CustomJWTAuthentication]

    def get(self, request):
        user = _current_user(request)
        if user:
            return _db_cart_response(request, user, 'Cart loaded')
        return _guest_cart_response(request, 'Cart loaded')


class StorefrontCartAddView(APIView):
    """POST /api/catalog/cart/add/  {product_id, quantity}"""

    authentication_classes = [CustomJWTAuthentication]

    def post(self, request):
        try:
            product_id = int(request.data.get('product_id'))
            quantity = max(1, int(request.data.get('quantity', 1)))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid product or quantity.'},
                            status=status.HTTP_400_BAD_REQUEST)

        product = get_product_or_none(product_id)
        if not product or not product.is_active:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if (product.stock_quantity or 0) <= 0:
            return Response({'error': 'This item is out of stock.'},
                            status=status.HTTP_400_BAD_REQUEST)

        quantity = min(quantity, product.stock_quantity)
        user = _current_user(request)

        if user:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(
                    user_id=user.user_id,
                    defaults={'created_at': timezone.now(), 'updated_at': timezone.now()},
                )
                item = CartItem.objects.filter(cart=cart, product=product).first()
                if item:
                    item.quantity = min(item.quantity + quantity, product.stock_quantity)
                    item.save(update_fields=['quantity'])
                else:
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=quantity,
                        added_at=timezone.now(),
                    )
                Cart.objects.filter(pk=cart.pk).update(updated_at=timezone.now())
            return _db_cart_response(request, user, 'Added to cart')

        cart = _guest_cart(request)
        key = str(product.product_id)
        cart[key] = min(cart.get(key, 0) + quantity, product.stock_quantity)
        _save_guest_cart(request, cart)
        return _guest_cart_response(request, 'Added to cart')


class StorefrontCartUpdateView(APIView):
    """POST /api/catalog/cart/update/ {product_id, quantity}  (0 removes)"""

    authentication_classes = [CustomJWTAuthentication]

    def post(self, request):
        try:
            product_id = int(request.data.get('product_id'))
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)

        user = _current_user(request)
        if user:
            cart, _ = Cart.objects.get_or_create(
                user_id=user.user_id,
                defaults={'created_at': timezone.now(), 'updated_at': timezone.now()},
            )
            item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
            if item:
                if quantity <= 0:
                    item.delete()
                else:
                    item.quantity = quantity
                    item.save(update_fields=['quantity'])
            return _db_cart_response(request, user)

        cart = _guest_cart(request)
        key = str(product_id)
        if quantity <= 0:
            cart.pop(key, None)
        else:
            cart[key] = quantity
        _save_guest_cart(request, cart)
        return _guest_cart_response(request)


# ══════════════════════════════════════════════════════════════
#  WISHLIST + RECENTLY VIEWED
# ══════════════════════════════════════════════════════════════
class WishlistView(APIView):
    """GET /api/catalog/wishlist/ · POST toggles a product."""

    def get(self, request):
        items = wishlist_products(request)
        return Response({'count': len(items), 'results': items,
                         'product_ids': wishlist_ids(request)})

    def post(self, request):
        try:
            product_id = int(request.data.get('product_id'))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid product.'}, status=status.HTTP_400_BAD_REQUEST)

        if not get_product_or_none(product_id):
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        in_wishlist = toggle_wishlist(request, product_id)
        return Response({
            'in_wishlist': in_wishlist,
            'message': 'Saved to wishlist' if in_wishlist else 'Removed from wishlist',
            'count': len(wishlist_ids(request)),
            'product_ids': wishlist_ids(request),
        })


class RecentlyViewedView(APIView):
    """GET /api/catalog/recently-viewed/ · POST records a product view."""

    def get(self, request):
        exclude = request.query_params.get('exclude')
        exclude_id = int(exclude) if (exclude or '').isdigit() else None
        items = recently_viewed(request, exclude_id=exclude_id)
        return Response({'count': len(items), 'results': items})

    def post(self, request):
        try:
            product_id = int(request.data.get('product_id'))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid product.'}, status=status.HTTP_400_BAD_REQUEST)
        push_recently_viewed(request, product_id)
        return Response({'ok': True})
