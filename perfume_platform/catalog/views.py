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


def deduplicate_shop_products(products):
    """Return one representative product variant per perfume for the Shop.

    Product stores each size/variant as a separate row (for example 5ml and
    10ml). The Shop catalog is perfume-level, so only the first product for
    each perfume should be rendered. ProductListView orders by volume before
    calling this helper, making the smallest matching variant the card.
    """
    unique = []
    seen_perfumes = set()
    for product in products:
        perfume_id = getattr(product, 'perfume_id', None)
        if perfume_id is None and getattr(product, 'perfume', None) is not None:
            perfume_id = getattr(product.perfume, 'perfume_id', None)
        if perfume_id in seen_perfumes:
            continue
        seen_perfumes.add(perfume_id)
        unique.append(product)
    return unique


class ProductListView(APIView):
    """
    GET /api/catalog/products/
    Returns products with search, filtering, and pagination.
    
    Query parameters:
    - search: search by product name, brand, or notes
    - brand_id: filter by brand (repeatable: ?brand_id=1&brand_id=3)
    - min_price: filter by minimum price
    - max_price: filter by maximum price
    - product_type: filter by type (e.g., "decant", "full_bottle")
    - concentration: filter by concentration, repeatable (EDT, EDP, Parfum, EDC)
    - gender: filter by target gender, repeatable (Male, Female, Unisex)
    - season: filter by recommended season, repeatable (Spring, Summer, Fall, Winter, All Season)
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
        
        # Brand filter — supports selecting more than one brand checkbox
        # (?brand_id=1&brand_id=3), not just a single value.
        brand_ids = request.query_params.getlist('brand_id')
        if brand_ids:
            products = products.filter(perfume__brand_id__in=brand_ids)
        
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
        
        # Product type filter (e.g., decant, full_bottle)
        product_type = request.query_params.get('product_type')
        if product_type:
            products = products.filter(product_type=product_type)

        # Exact volume filter used by the Home page's Shop by Size links.
        volume = request.query_params.get('volume')
        if volume:
            try:
                products = products.filter(volume_ml=float(volume))
            except (ValueError, TypeError):
                pass

        # Concentration filter (EDT, EDP, Parfum, EDC) — checkboxes, multi-select
        concentrations = request.query_params.getlist('concentration')
        if concentrations:
            products = products.filter(perfume__concentration__in=concentrations)

        # Gender filter (Male, Female, Unisex) — checkboxes, multi-select
        genders = request.query_params.getlist('gender')
        if genders:
            products = products.filter(perfume__target_gender__in=genders)

        # Season filter (Spring, Summer, Fall, Winter, All Season) — checkboxes, multi-select
        seasons = [s.strip() for s in request.query_params.getlist('season') if s.strip()]
        if seasons:
            season_query = Q()
            for season in seasons:
                season_query |= Q(perfume__recommended_season__icontains=season)
            products = products.filter(season_query)
        
        # Stock filter (only show in-stock items)
        products = products.filter(stock_quantity__gt=0)

        # The Shop represents a PERFUME, not every size/variant row.
        # A perfume may have 5ml, 10ml, 20ml, etc. Product rows, but the Shop
        # should render that perfume once. The smallest matching variant is
        # used as the representative card; the detail endpoint still returns
        # all variants so customers can choose a size.
        products = products.order_by('perfume_id', 'volume_ml', 'product_id')
        unique_products = deduplicate_shop_products(products)

        # Apply pagination AFTER deduplication so the count and page ranges
        # represent unique perfumes rather than variant rows.
        try:
            limit = min(max(int(request.query_params.get('limit', 50)), 1), 100)
        except (TypeError, ValueError):
            limit = 50
        try:
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except (TypeError, ValueError):
            offset = 0

        total_count = len(unique_products)
        paginated_products = unique_products[offset:offset + limit]

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