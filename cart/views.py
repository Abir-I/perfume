"""
Cart Views
API endpoints for cart management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Cart, CartItem, Coupon
from catalog.models import Product
from django.utils import timezone


class CartListView(APIView):
    """Get cart items"""
    
    def get(self, request):
        """Get current user's cart"""
        try:
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                cart, created = Cart.objects.get_or_create(session_key=session_key)
            
            items = cart.items.all()
            
            # Calculate totals
            subtotal = cart.get_total_price()
            shipping = 0  # Free shipping
            tax = 0  # Calculate if needed
            total = subtotal + shipping + tax
            
            return Response({
                'cart_id': cart.id,
                'items': [
                    {
                        'id': item.id,
                        'product_id': item.product.product_id,
                        'product_name': item.product.perfume.perfume_name,
                        'brand': item.product.perfume.brand.brand_name,
                        'price': float(item.product.price),
                        'final_price': float(getattr(item.product.perfume, 'final_price', item.product.price)),
                        'quantity': item.quantity,
                        'image': str(item.product.perfume.image) if item.product.perfume.image else None,
                        'subtotal': float(item.get_subtotal()),
                    }
                    for item in items
                ],
                'subtotal': float(subtotal),
                'shipping': shipping,
                'tax': tax,
                'total_price': float(total),
                'total_items': cart.get_total_items(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddToCartView(APIView):
    """Add item to cart"""
    
    def post(self, request):
        """Add product to cart"""
        try:
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))
            
            if not product_id:
                return Response({'error': 'Product ID required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if quantity <= 0:
                return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            product = Product.objects.get(product_id=product_id)
            
            # Stock validation
            if product.quantity < quantity:
                return Response({
                    'error': f'Insufficient stock. Available: {product.quantity}',
                    'available_quantity': product.quantity
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                cart, created = Cart.objects.get_or_create(session_key=session_key)
            
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not item_created:
                # Check if adding more would exceed stock
                total_quantity = cart_item.quantity + quantity
                if product.quantity < total_quantity:
                    return Response({
                        'error': f'Cannot add {quantity} more. Total would be {total_quantity}, but only {product.quantity} available',
                        'available_quantity': product.quantity
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                cart_item.quantity += quantity
                cart_item.save()
            
            cart.updated_at = timezone.now()
            cart.save()
            
            return Response({
                'message': 'Item added to cart',
                'cart_id': cart.id,
                'total_items': cart.get_total_items(),
                'total_price': cart.get_total_price(),
            }, status=status.HTTP_201_CREATED)
        
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    """Update cart item quantity"""
    
    def patch(self, request, item_id):
        """Update quantity"""
        try:
            quantity = int(request.data.get('quantity', 1))
            
            if quantity < 0:
                return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item = CartItem.objects.get(id=item_id)
            cart = cart_item.cart
            
            if quantity == 0:
                cart_item.delete()
                message = 'Item removed from cart'
            else:
                cart_item.quantity = quantity
                cart_item.save()
                message = 'Quantity updated'
            
            # Get updated cart data
            items = cart.items.all()
            subtotal = cart.get_total_price()
            shipping = 0  # Free shipping
            tax = 0
            total = subtotal + shipping + tax
            
            return Response({
                'message': message,
                'items': [
                    {
                        'id': item.id,
                        'product_id': item.product.product_id,
                        'product_name': item.product.perfume.perfume_name,
                        'brand': item.product.perfume.brand.brand_name,
                        'price': float(item.product.price),
                        'final_price': float(getattr(item.product.perfume, 'final_price', item.product.price)),
                        'quantity': item.quantity,
                        'image': str(item.product.perfume.image) if item.product.perfume.image else None,
                        'subtotal': float(item.get_subtotal()),
                    }
                    for item in items
                ],
                'subtotal': float(subtotal),
                'shipping': shipping,
                'tax': tax,
                'total_price': float(total),
                'total_items': cart.get_total_items(),
            })
        
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromCartView(APIView):
    """Remove item from cart"""
    
    def delete(self, request, item_id):
        """Remove item"""
        try:
            cart_item = CartItem.objects.get(id=item_id)
            cart = cart_item.cart
            cart_item.delete()
            
            # Get updated cart data
            items = cart.items.all()
            subtotal = cart.get_total_price()
            shipping = 0  # Free shipping
            tax = 0
            total = subtotal + shipping + tax
            
            return Response({
                'message': 'Item removed from cart',
                'items': [
                    {
                        'id': item.id,
                        'product_id': item.product.product_id,
                        'product_name': item.product.perfume.perfume_name,
                        'brand': item.product.perfume.brand.brand_name,
                        'price': float(item.product.price),
                        'final_price': float(getattr(item.product.perfume, 'final_price', item.product.price)),
                        'quantity': item.quantity,
                        'image': str(item.product.perfume.image) if item.product.perfume.image else None,
                        'subtotal': float(item.get_subtotal()),
                    }
                    for item in items
                ],
                'subtotal': float(subtotal),
                'shipping': shipping,
                'tax': tax,
                'total_price': float(total),
                'total_items': cart.get_total_items(),
            })
        
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClearCartView(APIView):
    """Clear entire cart"""
    
    def delete(self, request):
        """Clear cart"""
        try:
            if request.user.is_authenticated:
                cart = Cart.objects.get(user=request.user)
            else:
                session_key = request.session.session_key
                cart = Cart.objects.get(session_key=session_key)
            
            CartItem.objects.filter(cart=cart).delete()
            
            return Response({'message': 'Cart cleared'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

