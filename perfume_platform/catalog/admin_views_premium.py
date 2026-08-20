"""Premium admin API using the real product/perfume schema.

The previous implementation referenced a removed discount/feature schema
(`discount_value`, `is_featured`, `final_price`, etc.).  This version exposes
only fields that actually exist in the database.
"""
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.authentication import CustomJWTAuthentication
from accounts.permissions import IsAdminRole
from accounts.models import Product, Brand, Perfume, CustomerOrder, Review
from .serializers import ProductSerializer


class AdminProductListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = Product.objects.select_related('perfume__brand').all().order_by('-product_id')
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(perfume__perfume_name__icontains=search)
        return Response({'count': qs.count(), 'results': ProductSerializer(qs, many=True).data})


class AdminProductDetailView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request, product_id):
        try:
            product = Product.objects.select_related('perfume__brand').get(product_id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        data = ProductSerializer(product).data
        data.update({'is_active': bool(product.is_active), 'stock_quantity': product.stock_quantity})
        return Response(data)


class AdminUpdateDiscountView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, product_id):
        return Response({'error': 'Discount fields are not part of the current database schema.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminUpdateStockView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            stock = int(request.data.get('stock_quantity', product.stock_quantity))
        except (TypeError, ValueError):
            return Response({'error': 'stock_quantity must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        if stock < 0:
            return Response({'error': 'Stock cannot be negative'}, status=status.HTTP_400_BAD_REQUEST)
        product.stock_quantity = stock
        if 'is_active' in request.data:
            product.is_active = 1 if str(request.data.get('is_active')).lower() in ('1', 'true', 'yes', 'on') else 0
        product.save(update_fields=['stock_quantity', 'is_active'])
        return Response({'success': True, 'stock_quantity': product.stock_quantity, 'is_active': bool(product.is_active)})


class AdminUpdateFeaturesView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, product_id):
        return Response({'error': 'Feature flags are not part of the current database schema.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminDashboardStatsView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        total_products = Product.objects.count()
        return Response({
            'total_products': total_products,
            'in_stock': Product.objects.filter(stock_quantity__gt=0, is_active=1).count(),
            'out_of_stock': Product.objects.filter(stock_quantity__lte=0).count(),
            'inactive': Product.objects.filter(is_active=0).count(),
            'low_stock': Product.objects.filter(stock_quantity__gt=0, stock_quantity__lte=5).count(),
            'brands': Brand.objects.count(),
            'perfumes': Perfume.objects.count(),
            'orders': CustomerOrder.objects.count(),
            'reviews': Review.objects.count(),
            'on_discount': 0,
            'limited_edition': 0,
        })


class AdminBulkOperationView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request):
        ids = request.data.get('product_ids') or []
        operation = request.data.get('operation')
        qs = Product.objects.filter(product_id__in=ids)
        if not ids or not operation:
            return Response({'error': 'product_ids and operation are required'}, status=status.HTTP_400_BAD_REQUEST)
        if operation == 'activate':
            count = qs.update(is_active=1)
        elif operation == 'deactivate':
            count = qs.update(is_active=0)
        elif operation == 'set_stock':
            try:
                value = int(request.data.get('value'))
            except (TypeError, ValueError):
                return Response({'error': 'value must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
            if value < 0:
                return Response({'error': 'Stock cannot be negative'}, status=status.HTTP_400_BAD_REQUEST)
            count = qs.update(stock_quantity=value)
        else:
            return Response({'error': 'Unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'updated': count})
