"""
Orders Views - Complete Order Management API
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import CustomerOrder, OrderItem, OrderTracking, Payment, Invoice, OrderStatus
from cart.models import Cart, CartItem
from catalog.models import Product
import random
import string


def generate_order_number():
    """Generate unique order number"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{timestamp}-{random_suffix}"


def generate_tracking_number():
    """Generate tracking number"""
    return 'TRK' + ''.join(random.choices(string.digits, k=12))


class OrderListView(APIView):
    """List user's orders"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            orders = CustomerOrder.objects.filter(user=request.user)
            
            return Response({
                'orders': [
                    {
                        'order_id': order.order_id,
                        'order_number': order.order_number,
                        'order_date': order.order_date.isoformat(),
                        'total_amount': float(order.total_amount),
                        'order_status': order.order_status,
                        'status_display': order.get_status_display_fancy(),
                        'items_count': order.items.count(),
                        'can_cancel': order.can_cancel(),
                        'customer_name': order.customer_name,
                    }
                    for order in orders
                ]
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """Get order details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = get_object_or_404(CustomerOrder, order_id=order_id, user=request.user)
            
            tracking_history = OrderTracking.objects.filter(order=order)
            
            return Response({
                'order': {
                    'order_id': order.order_id,
                    'order_number': order.order_number,
                    'order_date': order.order_date.isoformat(),
                    'total_amount': float(order.total_amount),
                    'subtotal': float(order.subtotal),
                    'shipping_cost': float(order.shipping_cost),
                    'tax': float(order.tax),
                    'order_status': order.order_status,
                    'status_display': order.get_status_display_fancy(),
                    'payment_status': order.payment_status,
                    'payment_method': order.payment_method,
                    'customer_name': order.customer_name,
                    'customer_email': order.customer_email,
                    'customer_phone': order.customer_phone,
                    'shipping_address': order.shipping_address,
                    'shipping_city': order.shipping_city,
                    'shipping_state': order.shipping_state,
                    'shipping_postal_code': order.shipping_postal_code,
                    'tracking_number': order.tracking_number,
                    'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                    'shipped_date': order.shipped_date.isoformat() if order.shipped_date else None,
                    'delivered_date': order.delivered_date.isoformat() if order.delivered_date else None,
                    'courier_name': order.courier_name,
                    'is_cancelled': order.is_cancelled,
                    'can_cancel': order.can_cancel(),
                    'items': [
                        {
                            'product_name': item.product_name,
                            'product_brand': item.product_brand,
                            'product_image': item.product_image,
                            'quantity': item.quantity,
                            'unit_price': float(item.unit_price),
                            'total_price': float(item.total_price),
                        }
                        for item in order.items.all()
                    ],
                    'tracking_history': [
                        {
                            'status': th.status,
                            'status_message': th.status_message,
                            'timestamp': th.timestamp.isoformat(),
                            'location': th.location,
                        }
                        for th in tracking_history
                    ]
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    """Cancel order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = get_object_or_404(CustomerOrder, order_id=order_id, user=request.user)
            
            if not order.can_cancel():
                return Response(
                    {'error': f'Order cannot be cancelled (status: {order.order_status})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cancellation_reason = request.data.get('reason', 'Customer requested cancellation')
            
            order.is_cancelled = True
            order.order_status = OrderStatus.CANCELLED
            order.cancellation_reason = cancellation_reason
            order.cancelled_date = timezone.now()
            order.save()
            
            # Restore stock for all items in the order
            for item in order.items.all():
                if item.product:
                    product = item.product
                    product.quantity += item.quantity
                    
                    # Update stock status back to in_stock
                    perfume = product.perfume
                    if product.quantity > 0:
                        if product.quantity <= perfume.low_stock_threshold:
                            perfume.stock_status = 'low_stock'
                        else:
                            perfume.stock_status = 'in_stock'
                        perfume.save()
                    
                    product.save()
            
            # Add tracking record
            OrderTracking.objects.create(
                order=order,
                status=OrderStatus.CANCELLED,
                status_message=cancellation_reason,
                location='Customer'
            )
            
            # Refund if payment was completed
            if order.payment and order.payment.payment_status == 'completed':
                order.payment.payment_status = 'refunded'
                order.payment.refund_date = timezone.now()
                order.payment.save()
            
            return Response({
                'message': 'Order cancelled successfully',
                'order_number': order.order_number,
                'new_status': order.order_status
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckoutView(APIView):
    """Checkout and create order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            cart = Cart.objects.get(user=user)
            cart_items = cart.items.all()
            
            if not cart_items.exists():
                return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get order details
            customer_name = request.data.get('name', user.get_full_name() or user.username)
            customer_email = request.data.get('email', user.email)
            customer_phone = request.data.get('phone', '')
            shipping_address = request.data.get('address', '')
            shipping_city = request.data.get('city', '')
            shipping_state = request.data.get('state', '')
            shipping_postal_code = request.data.get('postal_code', '')
            payment_method = request.data.get('payment_method', 'cod')
            
            # Calculate totals
            subtotal = sum(item.get_subtotal() for item in cart_items)
            shipping_cost = 50 if subtotal > 0 else 0
            tax = subtotal * 0.05
            discount_amount = 0
            total_amount = subtotal + shipping_cost + tax - discount_amount
            
            # Create order
            order = CustomerOrder.objects.create(
                user=user,
                order_number=generate_order_number(),
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_postal_code=shipping_postal_code,
                payment_method=payment_method,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                discount_amount=discount_amount,
                total_amount=total_amount,
                order_status=OrderStatus.PENDING,
            )
            
            # Add tracking record
            OrderTracking.objects.create(
                order=order,
                status=OrderStatus.PENDING,
                status_message='Order received',
                location='Order System'
            )
            
            # Add items to order and reduce stock
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.perfume.perfume_name,
                    product_brand=cart_item.product.perfume.brand.brand_name,
                    product_image=str(cart_item.product.perfume.image),
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price,
                    total_price=cart_item.get_subtotal(),
                )
                
                # CRITICAL: Reduce stock after order
                product = cart_item.product
                product.quantity -= cart_item.quantity
                
                # Update product stock status
                if product.quantity <= 0:
                    product.quantity = 0
                    perfume = product.perfume
                    perfume.stock_status = 'out_of_stock'
                    perfume.save()
                elif product.quantity <= product.perfume.low_stock_threshold:
                    perfume = product.perfume
                    perfume.stock_status = 'low_stock'
                    perfume.save()
                
                product.save()
            
            # Create invoice
            Invoice.objects.create(
                order=order,
                invoice_number=f"INV-{order.order_number}",
                subtotal=subtotal,
                tax=tax,
                shipping=shipping_cost,
                discount=discount_amount,
                total=total_amount,
            )
            
            # Create payment record
            Payment.objects.create(
                order=order,
                payment_method=payment_method,
                amount=total_amount,
                payment_status='pending' if payment_method == 'cod' else 'completed',
            )
            
            # Clear cart
            CartItem.objects.filter(cart=cart).delete()
            
            return Response({
                'message': 'Order created successfully',
                'order_id': order.order_id,
                'order_number': order.order_number,
                'order_status': order.order_status,
                'total_amount': float(total_amount),
            }, status=status.HTTP_201_CREATED)
        
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
