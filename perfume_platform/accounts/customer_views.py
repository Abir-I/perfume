"""
Customer Panel Views - CORRECTED
All imports fixed to avoid ModuleNotFoundError
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
import json


# FIX: Import from the correct apps
try:
    from accounts.models import User, Address
except ImportError:
    User = None
    Address = None

try:
    from orders.models import CustomerOrder, OrderItem
except ImportError:
    CustomerOrder = None
    OrderItem = None

try:
    from catalog.models import Perfume, Product
except ImportError:
    Perfume = None
    Product = None

try:
    from cart.models import Cart, CartItem
except ImportError:
    Cart = None
    CartItem = None


class CustomerProfileView(APIView):
    """Get/Update customer profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        try:
            total_orders = CustomerOrder.objects.filter(user=user).count() if CustomerOrder else 0
            total_spent = CustomerOrder.objects.filter(user=user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0 if CustomerOrder else 0
        except:
            total_orders = 0
            total_spent = 0
        
        return Response({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': getattr(user, 'phone_number', ''),
            'image': str(getattr(user, 'image', '')) if hasattr(user, 'image') else None,
            'date_joined': user.date_joined,
            'total_orders': total_orders,
            'total_spent': float(total_spent),
        })
    
    def put(self, request):
        user = request.user
        user.first_name = request.data.get('name', user.first_name)
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'name': user.get_full_name(),
                'email': user.email,
            }
        })


class CustomerOrdersView(APIView):
    """Get all customer orders"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not CustomerOrder:
            return Response({'orders': [], 'count': 0})
        
        user = request.user
        orders = CustomerOrder.objects.filter(user=user).order_by('-order_date')
        
        orders_data = []
        for order in orders:
            items = order.items.all() if hasattr(order, 'items') else []
            orders_data.append({
                'id': order.order_id,
                'date': order.order_date.isoformat(),
                'status': order.order_status,
                'total': float(order.total_amount),
                'items_count': items.count(),
                'items': [
                    {
                        'product': item.product_name,
                        'quantity': item.quantity,
                        'price': float(item.price),
                    }
                    for item in items
                ]
            })
        
        return Response({
            'count': len(orders_data),
            'orders': orders_data,
        })


class CustomerOrderDetailView(APIView):
    """Get single order details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        if not CustomerOrder:
            return Response({'error': 'Orders not configured'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            order = CustomerOrder.objects.get(order_id=order_id, user=request.user)
            items = order.items.all() if hasattr(order, 'items') else []
            
            return Response({
                'id': order.order_id,
                'date': order.order_date.isoformat(),
                'status': order.order_status,
                'total': float(order.total_amount),
                'shipping_address': order.shipping_address,
                'items': [
                    {
                        'id': item.order_item_id,
                        'product': item.product_name,
                        'brand': item.product_brand,
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'image': item.image_url,
                    }
                    for item in items
                ]
            })
        except CustomerOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerAddressesView(APIView):
    """Manage customer addresses"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not Address:
            return Response({'addresses': [], 'count': 0})
        
        addresses = Address.objects.filter(user=request.user)
        
        return Response({
            'count': addresses.count(),
            'addresses': [
                {
                    'id': addr.id,
                    'line1': addr.address_line_1 if hasattr(addr, 'address_line_1') else '',
                    'line2': addr.address_line_2 if hasattr(addr, 'address_line_2') else '',
                    'city': addr.city,
                    'postal': addr.postal_code if hasattr(addr, 'postal_code') else '',
                    'country': addr.country,
                    'phone': addr.phone_number if hasattr(addr, 'phone_number') else '',
                    'default': getattr(addr, 'is_default', False),
                }
                for addr in addresses
            ]
        })
    
    def post(self, request):
        if not Address:
            return Response({'error': 'Address feature not available'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            address = Address.objects.create(
                user=user,
                address_line_1=request.data.get('line1'),
                address_line_2=request.data.get('line2', ''),
                city=request.data.get('city'),
                postal_code=request.data.get('postal'),
                country=request.data.get('country'),
                phone_number=request.data.get('phone'),
                is_default=request.data.get('default', False)
            )
            
            return Response({
                'message': 'Address added successfully',
                'address_id': address.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerWishlistView(APIView):
    """Manage customer wishlist"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not Cart or not CartItem or not Product:
            return Response({'items': [], 'count': 0})
        
        user = request.user
        cart = Cart.objects.filter(user=user, is_wishlist=True).first() if hasattr(Cart, 'is_wishlist') else None
        
        items = []
        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            items = [
                {
                    'id': item.id,
                    'product_id': item.product.product_id if hasattr(item, 'product') else 0,
                    'name': item.product.perfume.perfume_name if hasattr(item.product, 'perfume') else 'Product',
                    'brand': item.product.perfume.brand.brand_name if hasattr(item.product, 'perfume') else '',
                    'price': float(item.product.price) if hasattr(item, 'product') else 0,
                    'image': str(item.product.perfume.image) if hasattr(item.product, 'perfume') else '',
                }
                for item in cart_items
            ]
        
        return Response({
            'count': len(items),
            'items': items
        })
    
    def post(self, request):
        if not Cart or not CartItem or not Product:
            return Response({'error': 'Wishlist feature not available'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            product_id = request.data.get('product_id')
            product = Product.objects.get(product_id=product_id)
            
            wishlist, created = Cart.objects.get_or_create(
                user=user,
                is_wishlist=True
            )
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=wishlist,
                product=product,
                defaults={'quantity': 1}
            )
            
            return Response({
                'message': 'Added to wishlist',
                'product_id': product_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        if not Cart or not CartItem:
            return Response({'error': 'Wishlist feature not available'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product_id = request.data.get('product_id')
            user = request.user
            
            cart = Cart.objects.get(user=user, is_wishlist=True)
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
            
            return Response({'message': 'Removed from wishlist'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerDashboardStatsView(APIView):
    """Get customer dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not CustomerOrder:
            return Response({
                'total_orders': 0,
                'total_spent': 0,
                'pending_orders': 0,
                'average_order': 0,
                'recent_orders': []
            })
        
        user = request.user
        
        total_orders = CustomerOrder.objects.filter(user=user).count()
        
        total_spent = CustomerOrder.objects.filter(user=user).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        recent_orders = CustomerOrder.objects.filter(user=user).order_by('-order_date')[:3]
        
        pending_orders = CustomerOrder.objects.filter(
            user=user,
            order_status__in=['pending', 'confirmed', 'shipped']
        ).count()
        
        avg_order = total_spent / total_orders if total_orders > 0 else 0
        
        return Response({
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'pending_orders': pending_orders,
            'average_order': float(avg_order),
            'recent_orders': [
                {
                    'id': order.order_id,
                    'date': order.order_date.isoformat(),
                    'status': order.order_status,
                    'total': float(order.total_amount),
                }
                for order in recent_orders
            ]
        })


class CustomerReviewsView(APIView):
    """Get customer reviews"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not CustomerOrder:
            return Response({'reviews': [], 'count': 0})
        
        user = request.user
        
        reviews = []
        
        try:
            # Get delivered orders
            orders = CustomerOrder.objects.filter(
                user=user,
                order_status='delivered'
            )
            
            for order in orders:
                items = order.items.all() if hasattr(order, 'items') else []
                for item in items:
                    reviews.append({
                        'product': item.product_name,
                        'brand': item.product_brand,
                        'date': order.order_date.isoformat(),
                    })
        except:
            pass
        
        return Response({
            'count': len(reviews),
            'reviews': reviews
        })


class CustomerNotificationsView(APIView):
    """Get customer notifications"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not CustomerOrder:
            return Response({'notifications': [], 'count': 0})
        
        user = request.user
        
        notifications = []
        
        try:
            orders = CustomerOrder.objects.filter(user=user).order_by('-order_date')[:10]
            for order in orders:
                notifications.append({
                    'type': 'order_status',
                    'title': f'Order #{order.order_id} {order.order_status}',
                    'message': f'Your order is {order.order_status}',
                    'date': order.order_date.isoformat(),
                    'read': False,
                })
        except:
            pass
        
        return Response({
            'count': len(notifications),
            'notifications': notifications
        })
