from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from accounts.models import Brand, Perfume, Product
from .serializers import BrandSerializer, PerfumeSerializer, ProductSerializer


class BrandListView(APIView):
    """
    GET /api/catalog/brands/
    Returns all perfume brands
    """
    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response({
            'count': brands.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class ProductListView(APIView):
    """
    GET /api/catalog/products/
    Returns products with search, filtering, and pagination.
    
    Query parameters:
    - search: search by product name, brand, or notes
    - brand_id: filter by brand
    - min_price: filter by minimum price
    - max_price: filter by maximum price
    - product_type: filter by type (e.g., "decant", "full_size")
    - page: pagination page number (default: 1)
    """
    def get(self, request):
        products = Product.objects.select_related('perfume', 'perfume__brand').filter(is_active=1)
        
        # Search filter
        search_query = request.query_params.get('search', '').strip()
        if search_query:
            products = products.filter(
                Q(perfume__perfume_name__icontains=search_query) |
                Q(perfume__brand__brand_name__icontains=search_query) |
                Q(perfume__top_notes__icontains=search_query) |
                Q(perfume__middle_notes__icontains=search_query) |
                Q(perfume__base_notes__icontains=search_query)
            )
        
        # Brand filter
        brand_id = request.query_params.get('brand_id')
        if brand_id:
            products = products.filter(perfume__brand_id=brand_id)
        
        # Price range filter
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        
        # Product type filter (e.g., decant, full_size)
        product_type = request.query_params.get('product_type')
        if product_type:
            products = products.filter(product_type=product_type)
        
        # Stock filter (only show in-stock items)
        products = products.filter(stock_quantity__gt=0)
        
        # Pagination (simple: return first 50 by default)
        limit = min(int(request.query_params.get('limit', 50)), 100)
        offset = int(request.query_params.get('offset', 0))
        
        total_count = products.count()
        paginated_products = products[offset:offset + limit]
        
        serializer = ProductSerializer(paginated_products, many=True)
        
        return Response({
            'count': total_count,
            'results': serializer.data,
            'offset': offset,
            'limit': limit
        }, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """
    GET /api/catalog/products/<product_id>/
    Returns details of a single product
    """
    def get(self, request, product_id):
        try:
            product = Product.objects.select_related('perfume', 'perfume__brand').get(product_id=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PerfumeDetailView(APIView):
    """
    GET /api/catalog/perfumes/<perfume_id>/
    Returns details of a perfume and all its product variants
    """
    def get(self, request, perfume_id):
        try:
            perfume = Perfume.objects.select_related('brand').get(perfume_id=perfume_id)
            perfume_serializer = PerfumeSerializer(perfume)
            
            # Get all product variants (5ml, 10ml, 20ml, full size, etc.)
            products = Product.objects.filter(perfume_id=perfume_id, is_active=1, stock_quantity__gt=0)
            product_serializer = ProductSerializer(products, many=True)
            
            return Response({
                'perfume': perfume_serializer.data,
                'variants': product_serializer.data
            }, status=status.HTTP_200_OK)
        except Perfume.DoesNotExist:
            return Response(
                {'error': 'Perfume not found'},
                status=status.HTTP_404_NOT_FOUND
            )