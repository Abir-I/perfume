"""Canonical end-to-end order API.

Core order tables remain accounts.CustomerOrder/OrderItem/Payment/Invoice.
The orders app adds only snapshots/history needed for a production-safe flow.
"""
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.authentication import CustomJWTAuthentication
from accounts.models import User, Address, Cart, CartItem, CustomerOrder, OrderItem, Payment, Invoice, Product
from .models import (
    OrderStatus, OrderShippingSnapshot, OrderFinancialSnapshot,
    OrderItemSnapshot, OrderStatusHistory, ReturnRequest, ReturnStatus,
)


COD_METHOD = 'Cash'
SHIPPING_FEE = Decimal('0.00')  # Existing storefront advertises free shipping.
DISCOUNT = Decimal('0.00')
TAX = Decimal('0.00')


def order_number(order):
    return f'ORD-{order.order_id:06d}'


def snapshot_address(order):
    snap = getattr(order, 'shipping_snapshot', None)
    if snap:
        return snap
    address = order.address
    return {
        'name': f'{order.user.first_name} {order.user.last_name}'.strip(),
        'email': order.user.email,
        'phone': order.user.phone or '',
        'address_line1': address.address_line1,
        'address_line2': address.address_line2 or '',
        'city': address.city,
        'state': address.state or '',
        'postal_code': address.postal_code or '',
        'country': address.country,
    }


RETURN_WINDOW_DAYS = 7


def _delivered_at(order):
    delivered = OrderStatusHistory.objects.filter(
        order_id=order.order_id, status=OrderStatus.DELIVERED
    ).order_by('-created_at', '-history_id').first()
    return delivered.created_at if delivered else order.order_date


def get_return_info(order):
    request = ReturnRequest.objects.filter(order_id=order.order_id).first()
    eligible = order.status == OrderStatus.DELIVERED
    deadline = (_delivered_at(order) + timedelta(days=RETURN_WINDOW_DAYS)) if eligible else None
    if eligible and deadline and timezone.now() > deadline:
        eligible = False
    if request and request.status not in (ReturnStatus.CANCELLED, ReturnStatus.REJECTED):
        can_request = False
    else:
        can_request = eligible and request is None
    return {
        'exists': bool(request),
        'return_id': request.return_id if request else None,
        'status': request.status if request else None,
        'reason': request.reason if request else None,
        'details': request.details if request else None,
        'refund_amount': float(request.refund_amount) if request else None,
        'admin_note': request.admin_note if request else '',
        'requested_at': request.requested_at.isoformat() if request else None,
        'reviewed_at': request.reviewed_at.isoformat() if request and request.reviewed_at else None,
        'eligible': eligible,
        'can_request': can_request,
        'return_window_days': RETURN_WINDOW_DAYS,
        'deadline': deadline.isoformat() if deadline else None,
    }


def serialize_order(order, include_details=False):
    items = list(OrderItem.objects.select_related('product__perfume__brand').filter(order=order))
    financial = getattr(order, 'financial_snapshot', None)
    subtotal = financial.subtotal if financial else sum((Decimal(i.unit_price) * i.quantity for i in items), Decimal('0'))
    shipping = financial.shipping_cost if financial else Decimal('0')
    discount = financial.discount_amount if financial else Decimal('0')
    tax = financial.tax_amount if financial else Decimal('0')
    payload = {
        'id': order.order_id,
        'order_id': order.order_id,
        'number': order_number(order),
        'order_number': order_number(order),
        'date': order.order_date.isoformat() if order.order_date else None,
        'order_date': order.order_date.isoformat() if order.order_date else None,
        'total': float(order.total_amount),
        'total_amount': float(order.total_amount),
        'subtotal': float(subtotal),
        'shipping_cost': float(shipping),
        'discount': float(discount),
        'tax': float(tax),
        'status': order.status,
        'order_status': order.status,
        'status_display': order.status,
        'current_status': order.status,
        'items_count': len(items),
        'can_cancel': order.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED),
        'customer_name': f'{order.user.first_name} {order.user.last_name}'.strip(),
        'customer_phone': order.user.phone or '',
        'payment_method': COD_METHOD,
        'payment_status': 'Pending',
        'return_request': get_return_info(order),
    }
    if include_details:
        address = snapshot_address(order)
        if isinstance(address, dict):
            payload['shipping'] = {
                'name': address['name'],
                'email': address['email'],
                'phone': address['phone'],
                'address': address['address_line1'],
                'address_line1': address['address_line1'],
                'address_line2': address['address_line2'],
                'city': address['city'],
                'state': address['state'],
                'postal_code': address['postal_code'],
                'country': address['country'],
            }
        payment = Payment.objects.filter(order=order).first()
        invoice = Invoice.objects.filter(order=order).first()
        payload['payment_method'] = payment.payment_method if payment else COD_METHOD
        payload['payment_status'] = payment.status if payment else 'Pending'
        payload['invoice'] = {
            'invoice_id': invoice.invoice_id,
            'invoice_number': invoice.invoice_number,
            'issued_date': invoice.issued_date.isoformat() if invoice.issued_date else None,
            'total_amount': float(invoice.total_amount),
            'tax_amount': float(invoice.tax_amount),
            'status': invoice.status,
        } if invoice else None
        history = list(OrderStatusHistory.objects.filter(order=order).select_related('changed_by'))
        if not history:
            history = [type('LegacyHistory', (), {'status': order.status, 'note': 'Order placed', 'created_at': order.order_date, 'changed_by': None})()]
        payload['tracking'] = {'number': None, 'carrier': None}
        payload['tracking_history'] = [
            {
                'status': h.status,
                'message': h.note or h.status,
                'status_message': h.note or h.status,
                'timestamp': h.created_at.isoformat(),
                'location': None,
                'changed_by': (h.changed_by.email if h.changed_by else 'System'),
            }
            for h in history
        ]
        payload['status_timeline'] = [
            {'status': s, 'label': s, 'completed': _status_progress(order.status) >= _status_progress(s)}
            for s in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
        ]
    return payload


def _status_progress(status_value):
    sequence = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
    return sequence.index(status_value) if status_value in sequence else -1


def _write_status(order, new_status, changed_by=None, note=''):
    OrderStatusHistory.objects.create(order_id=order.order_id, status=new_status, changed_by=changed_by, note=note)


class OrderListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = CustomerOrder.objects.filter(user_id=request.user.user_id).select_related('address', 'user').order_by('-order_date')
        return Response({'total_orders': orders.count(), 'orders': [serialize_order(o) for o in orders]})


class OrderDetailView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_related('address', 'user'), order_id=order_id, user_id=request.user.user_id)
        items = list(OrderItem.objects.select_related('product__perfume__brand').filter(order=order))
        data = serialize_order(order, include_details=True)
        snapshots = {s.order_item_id: s for s in OrderItemSnapshot.objects.filter(order_item_id__in=[i.order_item_id for i in items])}
        data_items = []
        for item in items:
            snap = snapshots.get(item.order_item_id)
            product = item.product
            name = snap.product_name if snap else product.perfume.perfume_name
            brand = snap.brand_name if snap else product.perfume.brand.brand_name
            volume = float(snap.volume_ml) if snap else float(product.volume_ml)
            product_type = snap.product_type if snap else product.product_type
            image = snap.image_url if snap else product.perfume.image_url
            data_items.append({
                'id': item.order_item_id,
                'product_id': item.product_id,
                'name': name,
                'product_name': name,
                'brand': brand,
                'product_brand': brand,
                'volume_ml': volume,
                'product_type': product_type,
                'image': image,
                'product_image': image,
                'quantity': item.quantity,
                'price': float(item.unit_price),
                'unit_price': float(item.unit_price),
                'total': float(item.subtotal or (item.unit_price * item.quantity)),
                'subtotal': float(item.subtotal or (item.unit_price * item.quantity)),
            })
        data['address'] = data['shipping']
        data['shipping_address'] = data['shipping']['address_line1']
        data['shipping_city'] = data['shipping']['city']
        data['shipping_state'] = data['shipping']['state']
        data['shipping_postal_code'] = data['shipping']['postal_code']
        data['shipping_country'] = data['shipping']['country']
        data['notes'] = order.notes or ''
        data['items'] = data_items
        return Response({'order': data, 'items': data_items, 'tracking_history': data['tracking_history']})


class OrderTrackingView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_related('address', 'user'), order_id=order_id, user_id=request.user.user_id)
        return Response({'order': serialize_order(order, include_details=True)})


class CancelOrderView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_for_update(), order_id=order_id, user_id=request.user.user_id)
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            return Response({'error': f'Order cannot be cancelled (status: {order.status})'}, status=status.HTTP_400_BAD_REQUEST)
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
        Payment.objects.filter(order=order).update(status='Pending')
        Invoice.objects.filter(order=order).update(status='Cancelled')
        _write_status(order, OrderStatus.CANCELLED, request.user, reason)
        return Response({'message': 'Order cancelled successfully', 'order_id': order.order_id, 'order_status': order.status})


class ReturnRequestListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = CustomerOrder.objects.filter(user_id=request.user.user_id).select_related('user').order_by('-order_date')
        rows = []
        for order in orders:
            info = get_return_info(order)
            if info['exists']:
                rows.append({
                    'order_id': order.order_id,
                    'order_number': order_number(order),
                    'order_date': order.order_date.isoformat() if order.order_date else None,
                    'total_amount': float(order.total_amount),
                    **info,
                })
        return Response({'total_returns': len(rows), 'returns': rows})


class ReturnRequestView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder, order_id=order_id, user_id=request.user.user_id)
        return Response({'order_id': order.order_id, 'order_number': order_number(order), 'return_request': get_return_info(order)})

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_for_update(), order_id=order_id, user_id=request.user.user_id)
        info = get_return_info(order)
        if not info['can_request']:
            if order.status != OrderStatus.DELIVERED:
                return Response({'error': 'Returns can only be requested after an order is delivered.'}, status=status.HTTP_400_BAD_REQUEST)
            if info['exists']:
                return Response({'error': 'A return request already exists for this order.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': f'The {RETURN_WINDOW_DAYS}-day return window has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        reason = (request.data.get('reason') or '').strip()
        details = (request.data.get('details') or '').strip()
        allowed_reasons = {
            'Damaged product', 'Wrong product', 'Product not as described',
            'Quality issue', 'Changed my mind', 'Other',
        }
        if reason not in allowed_reasons:
            return Response({'error': 'Please choose a valid return reason.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(details) > 1000:
            return Response({'error': 'Return details must be 1000 characters or fewer.'}, status=status.HTTP_400_BAD_REQUEST)

        rr = ReturnRequest.objects.create(
            order_id=order.order_id,
            reason=reason,
            details=details,
            status=ReturnStatus.PENDING,
            refund_amount=order.total_amount,
        )
        return Response({
            'message': 'Return request submitted successfully.',
            'return_request': get_return_info(order),
            'return_id': rr.return_id,
        }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def delete(self, request, order_id):
        order = get_object_or_404(CustomerOrder, order_id=order_id, user_id=request.user.user_id)
        rr = get_object_or_404(ReturnRequest, order_id=order.order_id)
        if rr.status != ReturnStatus.PENDING:
            return Response({'error': 'Only a pending return request can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        rr.status = ReturnStatus.CANCELLED
        rr.reviewed_at = timezone.now()
        rr.save(update_fields=['status', 'reviewed_at', 'updated_at'])
        return Response({'message': 'Return request cancelled.', 'return_request': get_return_info(order)})


class InvoiceView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(
            CustomerOrder.objects.select_related('user', 'address'),
            order_id=order_id, user_id=request.user.user_id
        )
        invoice = get_object_or_404(Invoice, order=order)
        items = list(OrderItem.objects.select_related('product__perfume__brand').filter(order=order))
        snapshots = {s.order_item_id: s for s in OrderItemSnapshot.objects.filter(order_item_id__in=[i.order_item_id for i in items])}
        financial = getattr(order, 'financial_snapshot', None)
        address = snapshot_address(order)
        rows = []
        for item in items:
            snap = snapshots.get(item.order_item_id)
            product = item.product
            rows.append({
                'name': snap.product_name if snap else product.perfume.perfume_name,
                'brand': snap.brand_name if snap else product.perfume.brand.brand_name,
                'volume_ml': float(snap.volume_ml) if snap else float(product.volume_ml),
                'product_type': snap.product_type if snap else product.product_type,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal or item.unit_price * item.quantity),
            })
        return Response({
            'invoice': {
                'invoice_id': invoice.invoice_id,
                'invoice_number': invoice.invoice_number,
                'issued_date': invoice.issued_date.isoformat() if invoice.issued_date else None,
                'status': invoice.status,
                'tax_amount': float(invoice.tax_amount),
                'total_amount': float(invoice.total_amount),
            },
            'order': {
                'order_id': order.order_id,
                'order_number': order_number(order),
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'status': order.status,
                'customer_name': f'{order.user.first_name} {order.user.last_name}'.strip(),
                'email': order.user.email,
                'phone': order.user.phone or '',
            },
            'shipping': address,
            'items': rows,
            'subtotal': float(financial.subtotal if financial else sum((Decimal(i.unit_price) * i.quantity for i in items), Decimal('0'))),
            'shipping_cost': float(financial.shipping_cost if financial else 0),
            'discount': float(financial.discount_amount if financial else 0),
            'tax': float(financial.tax_amount if financial else invoice.tax_amount),
            'total': float(financial.total_amount if financial else order.total_amount),
            'payment_method': (Payment.objects.filter(order=order).values_list('payment_method', flat=True).first() or COD_METHOD),
            'payment_status': (Payment.objects.filter(order=order).values_list('status', flat=True).first() or 'Pending'),
        })


class CheckoutView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart = Cart.objects.select_for_update().filter(user_id=user.user_id).first()
        if not cart:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart_items = list(
            CartItem.objects.select_related('product__perfume__brand')
            .filter(cart=cart)
            .order_by('added_at')
        )
        if not cart_items:
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Lock the actual products so concurrent checkout cannot oversell stock.
        product_ids = [item.product_id for item in cart_items]
        locked_products = {
            p.product_id: p
            for p in Product.objects.select_for_update().select_related('perfume__brand').filter(product_id__in=product_ids)
        }
        for item in cart_items:
            product = locked_products.get(item.product_id)
            if not product:
                return Response({'error': 'A product in your cart no longer exists.'}, status=status.HTTP_400_BAD_REQUEST)
            if not product.is_active:
                return Response({'error': f'{product.perfume.perfume_name} is unavailable.'}, status=status.HTTP_400_BAD_REQUEST)
            if item.quantity > product.stock_quantity:
                return Response({'error': f'Only {product.stock_quantity} of {product.perfume.perfume_name} ({product.volume_ml}ml) are available.'}, status=status.HTTP_400_BAD_REQUEST)

        # COD only. Never trust a client asking for another payment method.
        payment_method = str(request.data.get('payment_method') or 'cod').lower()
        if payment_method not in ('cod', 'cash', 'cash_on_delivery'):
            return Response({'error': 'Only Cash on Delivery is currently available.'}, status=status.HTTP_400_BAD_REQUEST)

        name = (request.data.get('name') or f'{user.first_name} {user.last_name}').strip()
        email = (request.data.get('email') or user.email).strip()
        phone = (request.data.get('phone') or user.phone or '').strip()
        if not name or not email or not phone:
            return Response({'error': 'Full name, email and phone are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prefer a saved address. If none is supplied, create one from checkout fields.
        address_id = request.data.get('address_id')
        if address_id:
            try:
                address = Address.objects.get(address_id=int(address_id), user_id=user.user_id)
            except (ValueError, TypeError, Address.DoesNotExist):
                return Response({'error': 'Selected shipping address is invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            line1 = (request.data.get('address') or '').strip()
            city = (request.data.get('city') or '').strip()
            country = (request.data.get('country') or 'Bangladesh').strip()
            if not line1 or not city or not country:
                return Response({'error': 'Please select a saved address or provide address and city.'}, status=status.HTTP_400_BAD_REQUEST)
            address = Address.objects.create(
                user_id=user.user_id,
                address_line1=line1,
                address_line2=(request.data.get('address_line2') or '').strip() or None,
                city=city,
                state=(request.data.get('state') or '').strip() or None,
                postal_code=(request.data.get('postal_code') or '').strip() or None,
                country=country,
                is_default=1 if not Address.objects.filter(user_id=user.user_id, is_default=1).exists() else 0,
            )

        first_name, _, last_name = name.partition(' ')
        User.objects.filter(user_id=user.user_id).update(first_name=first_name, last_name=last_name or '', phone=phone)

        subtotal = sum((Decimal(locked_products[item.product_id].price) * item.quantity for item in cart_items), Decimal('0.00'))
        shipping = SHIPPING_FEE if subtotal > 0 else Decimal('0.00')
        discount = DISCOUNT
        tax = TAX
        total = subtotal + shipping + tax - discount
        if total < 0:
            total = Decimal('0.00')

        order = CustomerOrder.objects.create(
            user_id=user.user_id,
            address_id=address.address_id,
            order_date=timezone.now(),
            status=OrderStatus.PENDING,
            total_amount=total,
            notes=(request.data.get('notes') or '').strip() or None,
        )

        OrderShippingSnapshot.objects.create(
            order_id=order.order_id,
            name=name,
            email=email,
            phone=phone,
            address_line1=address.address_line1,
            address_line2=address.address_line2 or '',
            city=address.city,
            state=address.state or '',
            postal_code=address.postal_code or '',
            country=address.country,
        )
        OrderFinancialSnapshot.objects.create(
            order_id=order.order_id,
            subtotal=subtotal,
            shipping_cost=shipping,
            discount_amount=discount,
            tax_amount=tax,
            total_amount=total,
        )

        for item in cart_items:
            product = locked_products[item.product_id]
            line_total = Decimal(product.price) * item.quantity
            order_item = OrderItem.objects.create(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=item.quantity,
                unit_price=product.price,
            )
            OrderItemSnapshot.objects.create(
                order_item_id=order_item.order_item_id,
                product_name=product.perfume.perfume_name,
                brand_name=product.perfume.brand.brand_name,
                product_type=product.product_type,
                volume_ml=product.volume_ml,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=line_total,
                image_url=product.perfume.image_url or '',
            )
            product.stock_quantity -= item.quantity
            if product.stock_quantity <= 0:
                product.stock_quantity = 0
                product.is_active = 0
            product.save(update_fields=['stock_quantity', 'is_active'])

        Payment.objects.create(
            order_id=order.order_id,
            payment_date=timezone.now(),
            payment_method=COD_METHOD,
            amount=total,
            status='Pending',
        )
        Invoice.objects.create(
            order_id=order.order_id,
            invoice_number=f'INV-{order.order_id:06d}',
            issued_date=timezone.now(),
            total_amount=total,
            tax_amount=tax,
            status='Issued',
        )
        _write_status(order, OrderStatus.PENDING, None, 'Order placed')

        # Clear the canonical backend cart only after all order records exist.
        CartItem.objects.filter(cart_id=cart.cart_id).delete()
        return Response({
            'message': 'Order created successfully',
            'order_id': order.order_id,
            'order_number': order_number(order),
            'order_status': order.status,
            'payment_method': COD_METHOD,
            'payment_status': 'Pending',
            'subtotal': float(subtotal),
            'shipping_cost': float(shipping),
            'discount': float(discount),
            'tax': float(tax),
            'total_amount': float(total),
        }, status=status.HTTP_201_CREATED)
