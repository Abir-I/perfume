"""Customer dashboard API using only the canonical existing MySQL schema."""
from django.db.models import Sum
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .authentication import CustomJWTAuthentication
from .models import User, Address, Product, CustomerOrder, OrderItem, Review, Cart, CartItem
from orders.models import OrderStatusHistory, OrderItemSnapshot, OrderFinancialSnapshot, OrderShippingSnapshot, OrderStatus


class AuthenticatedAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]


def order_number(order):
    return f'ORD-{order.order_id:06d}'


def order_status(order):
    return order.status


def user_payload(user):
    return {
        'id': user.user_id,
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': f'{user.first_name} {user.last_name}'.strip(),
        'email': user.email,
        'phone': user.phone or '',
        'date_joined': user.created_at.isoformat() if user.created_at else None,
    }


def _wishlist_ids(request):
    primary = request.session.get('wishlist_products', [])
    legacy = request.session.get('wishlist_ids', [])
    values = []
    for raw in list(primary) + list(legacy):
        if str(raw).isdigit() and int(raw) not in values:
            values.append(int(raw))
    return values


def _save_wishlist_ids(request, ids):
    request.session['wishlist_products'] = ids
    request.session['wishlist_ids'] = ids
    request.session.modified = True


def order_payload(order):
    items = OrderItem.objects.filter(order=order)
    item_rows = list(items.select_related('product__perfume'))
    return {
        'id': order.order_id,
        'order_id': order.order_id,
        'number': order_number(order),
        'order_number': order_number(order),
        'date': order.order_date.isoformat() if order.order_date else None,
        'created_at': order.order_date.isoformat() if order.order_date else None,
        'total': float(order.total_amount),
        'total_amount': float(order.total_amount),
        'status': order_status(order),
        'order_status': order_status(order),
        'status_display': order_status(order),
        'items_count': len(item_rows),
        'items': [
            {
                'product_id': i.product_id,
                'product_name': i.product.perfume.perfume_name,
                'name': i.product.perfume.perfume_name,
                'quantity': i.quantity,
                'price': float(i.unit_price),
            } for i in item_rows
        ],
        'can_cancel': order.status in ('Pending', 'Confirmed'),
        'customer_name': f'{order.user.first_name} {order.user.last_name}'.strip(),
    }


class DashboardView(AuthenticatedAPIView):
    def get(self, request):
        user = request.user
        orders = CustomerOrder.objects.filter(user_id=user.user_id).order_by('-order_date')
        total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        reviews_qs = Review.objects.filter(user_id=user.user_id).select_related('product__perfume').order_by('-created_at')
        reviews = reviews_qs[:3]
        wishlist_count = len(_wishlist_ids(request))
        pending = orders.filter(status__in=['Pending', 'Confirmed', 'Processing', 'Shipped']).count()
        return Response({
            'user': user_payload(user),
            'stats': {
                'total_orders': orders.count(),
                'total_spent': float(total_spent),
                'pending_orders': pending,
                'recent_orders_count': min(orders.count(), 5),
                'total_reviews': reviews_qs.count(),
                'wishlist_count': wishlist_count,
            },
            'recent_orders': [order_payload(o) for o in orders[:5]],
            'recent_reviews': [
                {
                    'id': r.review_id,
                    'product_id': r.product_id,
                    'product': r.product.perfume.perfume_name,
                    'rating': r.rating,
                    'comment': r.comment or '',
                    'date': r.created_at.isoformat() if r.created_at else None,
                } for r in reviews
            ],
        })


class ProfileView(AuthenticatedAPIView):
    def get(self, request):
        return Response(user_payload(request.user))

    def put(self, request):
        user = request.user
        email = (request.data.get('email', user.email) or '').strip()
        if email != user.email and User.objects.filter(email=email).exclude(user_id=user.user_id).exists():
            return Response({'error': 'Email is already in use.'}, status=status.HTTP_400_BAD_REQUEST)
        user.first_name = (request.data.get('first_name', user.first_name) or '').strip()
        user.last_name = (request.data.get('last_name', user.last_name) or '').strip()
        user.email = email
        user.phone = (request.data.get('phone', user.phone) or '').strip()
        user.save(update_fields=['first_name', 'last_name', 'email', 'phone'])
        return Response({'message': 'Profile updated successfully', 'user': user_payload(user)})


class OrdersListView(AuthenticatedAPIView):
    def get(self, request):
        orders = CustomerOrder.objects.filter(user_id=request.user.user_id).order_by('-order_date')
        return Response({'total_orders': orders.count(), 'orders': [order_payload(o) for o in orders]})


class OrderDetailView(AuthenticatedAPIView):
    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_related('address', 'user'), order_id=order_id, user_id=request.user.user_id)
        items = list(OrderItem.objects.select_related('product__perfume__brand').filter(order=order))
        snapshots = {s.order_item_id: s for s in OrderItemSnapshot.objects.filter(order_item_id__in=[i.order_item_id for i in items])}
        financial = getattr(order, 'financial_snapshot', None)
        shipping = getattr(order, 'shipping_snapshot', None)
        payment = __import__('accounts.models', fromlist=['Payment']).Payment.objects.filter(order=order).first()
        history = list(OrderStatusHistory.objects.filter(order=order).select_related('changed_by'))
        address = {
            'address': shipping.address_line1 if shipping else order.address.address_line1,
            'address_line1': shipping.address_line1 if shipping else order.address.address_line1,
            'address_line2': shipping.address_line2 if shipping else (order.address.address_line2 or ''),
            'city': shipping.city if shipping else order.address.city,
            'state': shipping.state if shipping else (order.address.state or ''),
            'postal_code': shipping.postal_code if shipping else (order.address.postal_code or ''),
            'country': shipping.country if shipping else order.address.country,
            'name': shipping.name if shipping else f'{order.user.first_name} {order.user.last_name}'.strip(),
            'email': shipping.email if shipping else order.user.email,
            'phone': shipping.phone if shipping else (order.user.phone or ''),
        }
        payload = order_payload(order)
        payload.update({
            'payment_method': payment.payment_method if payment else 'Cash',
            'payment_status': payment.status if payment else 'Pending',
            'shipping': address,
            'address': address,
            'tracking': {'number': None, 'carrier': None},
            'current_status': order.status,
            'subtotal': float(financial.subtotal if financial else order.total_amount),
            'shipping_cost': float(financial.shipping_cost if financial else 0),
            'discount': float(financial.discount_amount if financial else 0),
            'tax': float(financial.tax_amount if financial else 0),
            'tracking_history': [
                {'status': h.status, 'message': h.note or h.status, 'timestamp': h.created_at.isoformat(), 'location': None}
                for h in history
            ],
        })
        data_items = []
        for i in items:
            snap = snapshots.get(i.order_item_id)
            p = i.product
            data_items.append({
                'id': i.order_item_id, 'product_id': i.product_id,
                'name': snap.product_name if snap else p.perfume.perfume_name,
                'product_name': snap.product_name if snap else p.perfume.perfume_name,
                'brand': snap.brand_name if snap else p.perfume.brand.brand_name,
                'quantity': i.quantity, 'price': float(i.unit_price), 'total': float(i.subtotal or i.unit_price*i.quantity),
                'volume_ml': float(snap.volume_ml) if snap else float(p.volume_ml),
                'product_type': snap.product_type if snap else p.product_type,
                'image': snap.image_url if snap else p.perfume.image_url,
            })
        return Response({'order': payload, 'items': data_items, 'tracking_history': payload['tracking_history']})


class OrderTrackingView(AuthenticatedAPIView):
    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder, order_id=order_id, user_id=request.user.user_id)
        history = list(OrderStatusHistory.objects.filter(order=order).order_by('created_at', 'history_id'))
        sequence = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
        if not history:
            history = [type('LegacyHistory', (), {'status': order.status, 'note': 'Order placed', 'created_at': order.order_date})()]
        current = sequence.index(order.status) if order.status in sequence else -1
        timeline = [{'status': s, 'label': s, 'completed': current >= i} for i, s in enumerate(sequence)]
        return Response({
            'order_number': order_number(order),
            'current_status': order.status,
            'status_display': order.status,
            'tracking_number': None,
            'courier_name': None,
            'estimated_delivery': None,
            'status_timeline': timeline,
            'tracking_history': [{'status': h.status, 'message': h.note or h.status, 'timestamp': h.created_at.isoformat(), 'location': None} for h in history],
        })


class OrderCancelView(AuthenticatedAPIView):
    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_for_update(), order_id=order_id, user_id=request.user.user_id)
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            return Response({'error': 'This order cannot be cancelled in its current status.'}, status=status.HTTP_400_BAD_REQUEST)
        reason = (request.data.get('reason') or 'Customer requested cancellation').strip()
        for item in OrderItem.objects.select_related('product').filter(order=order):
            product = item.product
            product.stock_quantity += item.quantity
            if product.stock_quantity > 0:
                product.is_active = 1
            product.save(update_fields=['stock_quantity', 'is_active'])
        order.status = OrderStatus.CANCELLED
        order.notes = f'{order.notes or ""}\nCancellation reason: {reason}'.strip()
        order.save(update_fields=['status', 'notes'])
        from .models import Payment, Invoice
        Payment.objects.filter(order=order).update(status='Pending')
        Invoice.objects.filter(order=order).update(status='Cancelled')
        OrderStatusHistory.objects.create(order_id=order.order_id, status=OrderStatus.CANCELLED, changed_by=request.user, note=reason)
        return Response({'message': 'Order cancelled successfully', 'order_id': order.order_id, 'status': order.status})


class ReviewsListView(AuthenticatedAPIView):
    def get(self, request):
        reviews = Review.objects.filter(user_id=request.user.user_id).select_related('product__perfume').order_by('-created_at')
        return Response({'total_reviews': reviews.count(), 'reviews': [
            {
                'id': r.review_id,
                'review_id': r.review_id,
                'product_id': r.product_id,
                'product_name': r.product.perfume.perfume_name,
                'rating': r.rating,
                'comment': r.comment or '',
                'is_verified_purchase': bool(r.is_verified_purchase),
                'created_at': r.created_at.isoformat() if r.created_at else None,
                'can_edit': True,
                'can_delete': True,
            } for r in reviews
        ]})


class ReviewCreateView(AuthenticatedAPIView):
    def post(self, request):
        user = request.user
        try:
            product_id = int(request.data.get('product_id'))
            rating = int(request.data.get('rating'))
        except (TypeError, ValueError):
            return Response({'error': 'product_id and rating are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if rating < 1 or rating > 5:
            return Response({'error': 'Rating must be between 1 and 5.'}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, product_id=product_id)
        purchased = OrderItem.objects.filter(order__user_id=user.user_id, order__status=OrderStatus.DELIVERED, product_id=product_id).exists()
        if not purchased:
            return Response({'error': 'You can review only products you have purchased.'}, status=status.HTTP_403_FORBIDDEN)
        if Review.objects.filter(user_id=user.user_id, product_id=product_id).exists():
            return Response({'error': 'You have already reviewed this product.'}, status=status.HTTP_400_BAD_REQUEST)
        review = Review.objects.create(
            user_id=user.user_id,
            product_id=product_id,
            rating=rating,
            comment=(request.data.get('comment') or '').strip() or None,
            created_at=timezone.now(),
            is_verified_purchase=1,
        )
        return Response({'message': 'Review created successfully', 'review_id': review.review_id}, status=status.HTTP_201_CREATED)


class ReviewUpdateView(AuthenticatedAPIView):
    def put(self, request, review_id):
        review = get_object_or_404(Review, review_id=review_id, user_id=request.user.user_id)
        try:
            rating = int(request.data.get('rating', review.rating))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid rating.'}, status=status.HTTP_400_BAD_REQUEST)
        if rating < 1 or rating > 5:
            return Response({'error': 'Rating must be between 1 and 5.'}, status=status.HTTP_400_BAD_REQUEST)
        review.rating = rating
        review.comment = (request.data.get('comment', review.comment) or '').strip() or None
        review.save(update_fields=['rating', 'comment'])
        return Response({'message': 'Review updated successfully', 'review_id': review.review_id})


class ReviewDeleteView(AuthenticatedAPIView):
    def delete(self, request, review_id):
        review = get_object_or_404(Review, review_id=review_id, user_id=request.user.user_id)
        review.delete()
        return Response({'message': 'Review deleted successfully'})


class WishlistView(AuthenticatedAPIView):
    """Session-backed wishlist. It requires no new DB table and is shared by the product-detail UI."""
    def get(self, request):
        ids = _wishlist_ids(request)
        products = Product.objects.select_related('perfume__brand').filter(product_id__in=ids)
        return Response({'wishlist_items': [
            {
                'product_id': p.product_id,
                'name': p.perfume.perfume_name,
                'brand': p.perfume.brand.brand_name,
                'price': float(p.price),
                'image': p.perfume.image_url,
            } for p in products
        ], 'total_items': products.count()})


class WishlistAddView(AuthenticatedAPIView):
    def post(self, request):
        product = get_object_or_404(Product, product_id=request.data.get('product_id'))
        ids = _wishlist_ids(request)
        if product.product_id not in ids:
            ids.append(product.product_id)
        _save_wishlist_ids(request, ids)
        return Response({'message': 'Added to wishlist', 'product_id': product.product_id}, status=status.HTTP_201_CREATED)


class WishlistRemoveView(AuthenticatedAPIView):
    def delete(self, request, product_id):
        ids = _wishlist_ids(request)
        ids = [x for x in ids if x != int(product_id)]
        _save_wishlist_ids(request, ids)
        return Response({'message': 'Removed from wishlist', 'product_id': int(product_id), 'total_items': len(ids)})


class AddressesView(AuthenticatedAPIView):
    def get(self, request):
        addresses = Address.objects.filter(user_id=request.user.user_id).order_by('-is_default', '-address_id')
        return Response({'addresses': [
            {
                'id': a.address_id,
                'address_id': a.address_id,
                'line1': a.address_line1,
                'line2': a.address_line2 or '',
                'city': a.city,
                'state': a.state or '',
                'postal_code': a.postal_code or '',
                'country': a.country,
                'default': bool(a.is_default),
            } for a in addresses
        ], 'total_addresses': addresses.count()})

    def post(self, request):
        line1 = (request.data.get('line1') or request.data.get('address_line1') or '').strip()
        city = (request.data.get('city') or '').strip()
        country = (request.data.get('country') or 'Bangladesh').strip()
        if not line1 or not city or not country:
            return Response({'error': 'Address line 1, city and country are required.'}, status=status.HTTP_400_BAD_REQUEST)
        address = Address.objects.create(
            user_id=request.user.user_id,
            address_line1=line1,
            address_line2=(request.data.get('line2') or '').strip() or None,
            city=city,
            state=(request.data.get('state') or '').strip() or None,
            postal_code=(request.data.get('postal_code') or request.data.get('postal') or '').strip() or None,
            country=country,
            is_default=1 if request.data.get('default') else 0,
        )
        if address.is_default:
            Address.objects.filter(user_id=request.user.user_id).exclude(address_id=address.address_id).update(is_default=0)
        return Response({'message': 'Address added successfully', 'address_id': address.address_id}, status=status.HTTP_201_CREATED)


class SettingsView(AuthenticatedAPIView):
    DEFAULTS = {
        'notifications': {'order_updates': True, 'promotional': False, 'reviews': True, 'wishlist_items': True},
        'preferences': {'language': 'en', 'currency': 'BDT', 'theme': 'light'},
    }

    def get(self, request):
        saved = request.session.get('account_settings', self.DEFAULTS)
        return Response(saved)

    def put(self, request):
        current = request.session.get('account_settings', self.DEFAULTS)
        notifications = request.data.get('notifications', current.get('notifications', {}))
        preferences = request.data.get('preferences', current.get('preferences', {}))
        current['notifications'] = {
            'order_updates': bool(notifications.get('order_updates', True)),
            'promotional': bool(notifications.get('promotional', False)),
            'reviews': bool(notifications.get('reviews', True)),
            'wishlist_items': bool(notifications.get('wishlist_items', True)),
        }
        current['preferences'] = {
            'language': str(preferences.get('language', 'en')),
            'currency': str(preferences.get('currency', 'BDT')),
            'theme': str(preferences.get('theme', 'light')),
        }
        request.session['account_settings'] = current
        request.session.modified = True
        return Response({'message': 'Settings updated successfully', **current})


class ActivityView(AuthenticatedAPIView):
    def get(self, request):
        user = request.user
        activities = [{'type': 'account', 'action': 'Joined', 'timestamp': user.created_at.isoformat(), 'details': 'Account created'}]
        for order in CustomerOrder.objects.filter(user_id=user.user_id).order_by('-order_date')[:10]:
            activities.append({'type': 'order', 'action': 'Order placed', 'timestamp': order.order_date.isoformat(), 'details': f'Order #{order_number(order)} - {order.total_amount} BDT', 'order_id': order.order_id})
        for review in Review.objects.filter(user_id=user.user_id).select_related('product__perfume').order_by('-created_at')[:10]:
            activities.append({'type': 'review', 'action': 'Review posted', 'timestamp': review.created_at.isoformat(), 'details': f'{review.rating}★ review for {review.product.perfume.perfume_name}'})
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response({'activities': activities, 'total_activities': len(activities)})
