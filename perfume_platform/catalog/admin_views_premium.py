# ═══════════════════════════════════════════════════════════════════════════════
# THE LAST NOTE - PREMIUM ADMIN VIEWS
# Version: 4.0 - Discounts, Offers, Limited Edition, Stock Management, Feature Tags
# ═══════════════════════════════════════════════════════════════════════════════

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F, DecimalField, Case, When, Value
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from accounts.models import Brand, Perfume, Product, User
from .serializers import BrandSerializer, PerfumeSerializer, ProductSerializer


class AdminProductListView(APIView):
    """
    GET /api/admin/products/
    Returns all products with admin details including discounts, offers, stock status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if user is admin/staff
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            products = Product.objects.select_related('perfume', 'perfume__brand').all()
            
            # Apply filters if provided
            search = request.query_params.get('search', '').strip()
            if search:
                products = products.filter(
                    Q(perfume__perfume_name__icontains=search) |
                    Q(perfume__brand__brand_name__icontains=search)
                )
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                if status_filter == 'in_stock':
                    products = products.filter(stock_quantity__gt=5)
                elif status_filter == 'low_stock':
                    products = products.filter(stock_quantity__gt=0, stock_quantity__lte=5)
                elif status_filter == 'out_of_stock':
                    products = products.filter(stock_quantity__lte=0)
            
            # Filter by feature
            feature_filter = request.query_params.get('feature')
            if feature_filter == 'on_discount':
                products = products.filter(discount_type__in=['percentage', 'fixed'])
            elif feature_filter == 'limited_edition':
                products = products.filter(is_limited_edition=True)
            elif feature_filter == 'featured':
                products = products.filter(is_featured=True)
            elif feature_filter == 'hot_deal':
                products = products.filter(is_hot_deal=True)
            
            # Prepare response
            products_data = []
            for product in products:
                final_price = product.price
                discount_percent = 0
                
                if product.discount_type == 'percentage' and product.discount_value:
                    discount_percent = product.discount_value
                    final_price = product.price * (1 - product.discount_value / 100)
                elif product.discount_type == 'fixed' and product.discount_value:
                    final_price = max(0, product.price - product.discount_value)
                
                products_data.append({
                    'product_id': product.product_id,
                    'perfume_name': product.perfume.perfume_name,
                    'brand_name': product.perfume.brand.brand_name,
                    'price': float(product.price),
                    'final_price': float(final_price),
                    'discount_type': product.discount_type,
                    'discount_value': float(product.discount_value) if product.discount_value else 0,
                    'discount_percent': discount_percent,
                    'stock_quantity': product.stock_quantity,
                    'is_limited_edition': bool(product.is_limited_edition),
                    'limited_edition_qty': product.limited_edition_qty,
                    'is_featured': bool(product.is_featured),
                    'is_hot_deal': bool(product.is_hot_deal),
                    'is_active': bool(product.is_active),
                    'discount_start_date': product.discount_start_date.isoformat() if product.discount_start_date else None,
                    'discount_end_date': product.discount_end_date.isoformat() if product.discount_end_date else None,
                    'image_url': product.image_url if product.image_url else '/static/images/placeholder.png',
                })
            
            return Response({
                'count': len(products_data),
                'results': products_data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminProductDetailView(APIView):
    """
    GET /api/admin/products/<product_id>/
    POST /api/admin/products/<product_id>/
    PUT /api/admin/products/<product_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, product_id):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            product = Product.objects.select_related('perfume', 'perfume__brand').get(product_id=product_id)
            
            final_price = product.price
            if product.discount_type == 'percentage' and product.discount_value:
                final_price = product.price * (1 - product.discount_value / 100)
            elif product.discount_type == 'fixed' and product.discount_value:
                final_price = max(0, product.price - product.discount_value)
            
            data = {
                'product_id': product.product_id,
                'perfume_name': product.perfume.perfume_name,
                'brand_id': product.perfume.brand.brand_id,
                'brand_name': product.perfume.brand.brand_name,
                'price': float(product.price),
                'final_price': float(final_price),
                'discount_type': product.discount_type,
                'discount_value': float(product.discount_value) if product.discount_value else 0,
                'stock_quantity': product.stock_quantity,
                'is_limited_edition': bool(product.is_limited_edition),
                'limited_edition_qty': product.limited_edition_qty,
                'is_featured': bool(product.is_featured),
                'is_hot_deal': bool(product.is_hot_deal),
                'is_active': bool(product.is_active),
                'discount_start_date': product.discount_start_date.isoformat() if product.discount_start_date else None,
                'discount_end_date': product.discount_end_date.isoformat() if product.discount_end_date else None,
                'image_url': product.image_url if product.image_url else '/static/images/placeholder.png',
                'product_type': product.product_type,
                'volume_ml': float(product.volume_ml) if product.volume_ml else 0,
            }
            
            return Response(data, status=status.HTTP_200_OK)
        
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminUpdateDiscountView(APIView):
    """
    POST /api/admin/products/<product_id>/update-discount/
    Updates discount information for a product
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            product = Product.objects.get(product_id=product_id)
            data = request.data
            
            # Update discount fields
            product.discount_type = data.get('discount_type', product.discount_type)
            product.discount_value = float(data.get('discount_value', 0)) if data.get('discount_value') else 0
            
            if product.discount_type == 'none':
                product.discount_value = 0
                product.discount_start_date = None
                product.discount_end_date = None
            else:
                if data.get('discount_start_date'):
                    product.discount_start_date = datetime.fromisoformat(data.get('discount_start_date'))
                if data.get('discount_end_date'):
                    product.discount_end_date = datetime.fromisoformat(data.get('discount_end_date'))
            
            product.save()
            
            final_price = product.price
            if product.discount_type == 'percentage' and product.discount_value:
                final_price = product.price * (1 - product.discount_value / 100)
            elif product.discount_type == 'fixed' and product.discount_value:
                final_price = max(0, product.price - product.discount_value)
            
            return Response({
                'success': True,
                'message': 'Discount updated successfully',
                'final_price': float(final_price)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminUpdateStockView(APIView):
    """
    POST /api/admin/products/<product_id>/update-stock/
    Updates stock information for a product
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            product = Product.objects.get(product_id=product_id)
            data = request.data
            
            product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
            product.is_active = bool(data.get('is_active', product.is_active))
            
            product.save()
            
            return Response({
                'success': True,
                'message': 'Stock updated successfully',
                'stock_quantity': product.stock_quantity,
                'is_active': product.is_active
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminUpdateFeaturesView(APIView):
    """
    POST /api/admin/products/<product_id>/update-features/
    Updates feature flags for a product (Limited Edition, Hot Deal, Featured)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            product = Product.objects.get(product_id=product_id)
            data = request.data
            
            product.is_limited_edition = bool(data.get('is_limited_edition', product.is_limited_edition))
            product.limited_edition_qty = int(data.get('limited_edition_qty', 0)) if product.is_limited_edition else 0
            product.is_featured = bool(data.get('is_featured', product.is_featured))
            product.is_hot_deal = bool(data.get('is_hot_deal', product.is_hot_deal))
            
            product.save()
            
            return Response({
                'success': True,
                'message': 'Features updated successfully',
                'is_limited_edition': product.is_limited_edition,
                'limited_edition_qty': product.limited_edition_qty,
                'is_featured': product.is_featured,
                'is_hot_deal': product.is_hot_deal
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminDashboardStatsView(APIView):
    """
    GET /api/admin/stats/
    Returns dashboard statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            total_products = Product.objects.count()
            in_stock = Product.objects.filter(stock_quantity__gt=0).count()
            out_of_stock = Product.objects.filter(stock_quantity__lte=0).count()
            low_stock = Product.objects.filter(stock_quantity__gt=0, stock_quantity__lte=5).count()
            
            on_discount = Product.objects.filter(discount_type__in=['percentage', 'fixed']).count()
            limited_edition = Product.objects.filter(is_limited_edition=True).count()
            featured = Product.objects.filter(is_featured=True).count()
            hot_deals = Product.objects.filter(is_hot_deal=True).count()
            
            # Calculate total discount value
            total_discount_value = 0
            for product in Product.objects.filter(discount_type__in=['percentage', 'fixed']):
                if product.discount_type == 'percentage':
                    total_discount_value += product.price * (product.discount_value / 100) if product.discount_value else 0
                else:
                    total_discount_value += product.discount_value or 0
            
            stats = {
                'total_products': total_products,
                'in_stock': in_stock,
                'out_of_stock': out_of_stock,
                'low_stock': low_stock,
                'on_discount': on_discount,
                'limited_edition': limited_edition,
                'featured': featured,
                'hot_deals': hot_deals,
                'total_discount_value': float(total_discount_value)
            }
            
            return Response(stats, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminBulkOperationView(APIView):
    """
    POST /api/admin/bulk-operation/
    Performs bulk operations on multiple products
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            if not (request.user.is_staff or request.user.user_type == 'admin'):
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
            data = request.data
            product_ids = data.get('product_ids', [])
            operation = data.get('operation')
            value = data.get('value')
            
            if not product_ids or not operation:
                return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
            
            products = Product.objects.filter(product_id__in=product_ids)
            count = 0
            
            if operation == 'mark_featured':
                products.update(is_featured=True)
                count = products.count()
            
            elif operation == 'mark_hot_deal':
                products.update(is_hot_deal=True)
                count = products.count()
            
            elif operation == 'mark_limited_edition':
                products.update(is_limited_edition=True, limited_edition_qty=int(value) if value else 100)
                count = products.count()
            
            elif operation == 'set_discount':
                discount_type = data.get('discount_type', 'percentage')
                discount_value = float(data.get('discount_value', 0))
                products.update(discount_type=discount_type, discount_value=discount_value)
                count = products.count()
            
            elif operation == 'activate':
                products.update(is_active=True)
                count = products.count()
            
            elif operation == 'deactivate':
                products.update(is_active=False)
                count = products.count()
            
            return Response({
                'success': True,
                'message': f'Operation applied to {count} products',
                'count': count
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
