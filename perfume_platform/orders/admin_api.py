from datetime import datetime, time
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.authentication import CustomJWTAuthentication
from accounts.permissions import IsAdminRole
from accounts.models import CustomerOrder, OrderItem, Payment, Invoice
from .models import OrderStatus, OrderStatusHistory, OrderFinancialSnapshot, OrderShippingSnapshot, OrderItemSnapshot, ReturnRequest, ReturnStatus
from .views import serialize_order, _write_status, get_return_info


class AdminOrderListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = CustomerOrder.objects.select_related('user', 'address').all().order_by('-order_date')
        search = request.query_params.get('search', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        if search:
            qs = qs.filter(Q(user__email__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search)).distinct()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_from:
            try:
                start = timezone.make_aware(datetime.combine(datetime.strptime(date_from, '%Y-%m-%d').date(), time.min))
                qs = qs.filter(order_date__gte=start)
            except ValueError:
                pass
        if date_to:
            try:
                end = timezone.make_aware(datetime.combine(datetime.strptime(date_to, '%Y-%m-%d').date(), time.max))
                qs = qs.filter(order_date__lte=end)
            except ValueError:
                pass
        orders = [serialize_order(o) for o in qs]
        return Response({'count': len(orders), 'results': orders, 'statuses': [s.value for s in OrderStatus]})


class AdminOrderDetailView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request, order_id):
        order = get_object_or_404(CustomerOrder.objects.select_related('user', 'address'), order_id=order_id)
        data = serialize_order(order, include_details=True)
        items = OrderItem.objects.select_related('product__perfume__brand').filter(order=order)
        snapshots = {s.order_item_id: s for s in OrderItemSnapshot.objects.filter(order_item_id__in=[i.order_item_id for i in items])}
        data['items'] = []
        for item in items:
            snap = snapshots.get(item.order_item_id)
            p = item.product
            data['items'].append({
                'order_item_id': item.order_item_id,
                'product_id': item.product_id,
                'name': snap.product_name if snap else p.perfume.perfume_name,
                'brand': snap.brand_name if snap else p.perfume.brand.brand_name,
                'volume_ml': float(snap.volume_ml) if snap else float(p.volume_ml),
                'product_type': snap.product_type if snap else p.product_type,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal or item.unit_price * item.quantity),
                'image_url': snap.image_url if snap else p.perfume.image_url,
            })
        history = OrderStatusHistory.objects.filter(order=order).select_related('changed_by')
        data['return_request'] = get_return_info(order)
        data['status_history'] = [
            {'status': h.status, 'note': h.note, 'timestamp': h.created_at.isoformat(), 'changed_by': h.changed_by.email if h.changed_by else 'System'}
            for h in history
        ]
        return Response(data)


class AdminOrderStatusUpdateView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def patch(self, request, order_id):
        new_status = str(request.data.get('status') or '').strip()
        note = str(request.data.get('note') or '').strip()
        if new_status not in {s.value for s in OrderStatus}:
            return Response({'error': 'Invalid order status.'}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(CustomerOrder.objects.select_for_update(), order_id=order_id)
        old_status = order.status
        if old_status == new_status:
            return Response({'message': 'Order status is already set.', 'order_status': old_status})

        allowed = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: set(),
            OrderStatus.CANCELLED: set(),
        }
        if new_status not in allowed.get(old_status, set()):
            return Response({'error': f'Invalid status transition: {old_status} → {new_status}.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status == OrderStatus.CANCELLED:
            for item in OrderItem.objects.select_related('product').filter(order=order):
                product = item.product
                product.stock_quantity += item.quantity
                if product.stock_quantity > 0:
                    product.is_active = 1
                product.save(update_fields=['stock_quantity', 'is_active'])
            Invoice.objects.filter(order=order).update(status='Cancelled')
        elif new_status == OrderStatus.DELIVERED:
            # COD is collected on delivery. Keep payment/invoice synchronized with the
            # business status instead of leaving a delivered order as unpaid.
            Payment.objects.filter(order=order).update(status='Completed')
            Invoice.objects.filter(order=order).update(status='Paid')

        order.status = new_status
        order.save(update_fields=['status'])
        _write_status(order, new_status, request.user, note or f'Status changed from {old_status} to {new_status}')
        return Response({'success': True, 'order_id': order.order_id, 'old_status': old_status, 'order_status': new_status})


class AdminOrderStatsView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = CustomerOrder.objects.all()
        return Response({
            'total': qs.count(),
            'pending': qs.filter(status=OrderStatus.PENDING).count(),
            'confirmed': qs.filter(status=OrderStatus.CONFIRMED).count(),
            'processing': qs.filter(status=OrderStatus.PROCESSING).count(),
            'shipped': qs.filter(status=OrderStatus.SHIPPED).count(),
            'delivered': qs.filter(status=OrderStatus.DELIVERED).count(),
            'cancelled': qs.filter(status=OrderStatus.CANCELLED).count(),
        })


class AdminReturnListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = ReturnRequest.objects.select_related('order__user').all().order_by('-requested_at')
        status_filter = request.query_params.get('status', '').strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        rows = [{
            'return_id': r.return_id,
            'order_id': r.order.order_id,
            'order_number': f'ORD-{r.order.order_id:06d}',
            'customer_name': f'{r.order.user.first_name} {r.order.user.last_name}'.strip(),
            'customer_email': r.order.user.email,
            'reason': r.reason,
            'details': r.details,
            'status': r.status,
            'refund_amount': float(r.refund_amount),
            'admin_note': r.admin_note,
            'requested_at': r.requested_at.isoformat() if r.requested_at else None,
            'reviewed_at': r.reviewed_at.isoformat() if r.reviewed_at else None,
        } for r in qs]
        return Response({'count': len(rows), 'results': rows, 'statuses': [s.value for s in ReturnStatus]})


class AdminReturnStatusUpdateView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def patch(self, request, return_id):
        new_status = str(request.data.get('status') or '').strip()
        note = str(request.data.get('admin_note') or '').strip()
        if new_status not in {s.value for s in ReturnStatus}:
            return Response({'error': 'Invalid return status.'}, status=status.HTTP_400_BAD_REQUEST)
        rr = get_object_or_404(ReturnRequest.objects.select_for_update().select_related('order'), return_id=return_id)
        if rr.status == ReturnStatus.CANCELLED:
            return Response({'error': 'A cancelled return request cannot be changed.'}, status=status.HTTP_400_BAD_REQUEST)
        if rr.status == ReturnStatus.REFUNDED and new_status != ReturnStatus.REFUNDED:
            return Response({'error': 'A refunded return request cannot be moved backwards.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == ReturnStatus.REFUNDED and rr.status not in (ReturnStatus.RECEIVED, ReturnStatus.REFUNDED):
            return Response({'error': 'Mark the return as Received before issuing a refund.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == ReturnStatus.RECEIVED and rr.status != ReturnStatus.APPROVED:
            return Response({'error': 'A return must be Approved before it can be marked Received.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == ReturnStatus.APPROVED and rr.status != ReturnStatus.PENDING:
            return Response({'error': 'Only pending return requests can be approved.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == ReturnStatus.REJECTED and rr.status != ReturnStatus.PENDING:
            return Response({'error': 'Only pending return requests can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == ReturnStatus.CANCELLED and rr.status != ReturnStatus.PENDING:
            return Response({'error': 'Only pending return requests can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        rr.status = new_status
        if note:
            rr.admin_note = note
        if new_status in (ReturnStatus.APPROVED, ReturnStatus.REJECTED, ReturnStatus.RECEIVED, ReturnStatus.REFUNDED, ReturnStatus.CANCELLED):
            rr.reviewed_at = timezone.now()
        if new_status == ReturnStatus.REFUNDED and rr.refund_amount <= 0:
            rr.refund_amount = rr.order.total_amount
        rr.save()
        if new_status == ReturnStatus.REFUNDED:
            Payment.objects.filter(order=rr.order).update(status='Refunded')
            Invoice.objects.filter(order=rr.order).update(status='Refunded')
        return Response({'success': True, 'return_id': rr.return_id, 'status': rr.status, 'refund_amount': float(rr.refund_amount)})
