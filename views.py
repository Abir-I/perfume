from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination

from accounts.models import Brand, Product
from .serializers import (
    BrandListSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class ProductListPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class BrandListView(generics.ListAPIView):
    """
    GET /api/catalog/brands/

    Returns every brand in the store. Used to populate filter
    dropdowns and nav menus on the frontend.
    """
    queryset = Brand.objects.all().order_by('brand_name')
    serializer_class = BrandListSerializer


class ProductListView(generics.ListAPIView):
    """
    GET /api/catalog/products/

    Returns active products, with optional filtering via query params:
      ?brand_id=<id>             e.g. /api/catalog/products/?brand_id=3
                                  (?brand=<id> also accepted, kept for
                                  backward compatibility with Sprint 3)
      ?size=<volume_ml>          e.g. /api/catalog/products/?size=5
      ?product_type=<type>       e.g. /api/catalog/products/?product_type=decant
      ?min_price=<price>         e.g. /api/catalog/products/?min_price=500
      ?max_price=<price>         e.g. /api/catalog/products/?max_price=1000
      ?limit=&offset=            pagination, default 20/page, max 100

    Filters can be combined, e.g.:
      /api/catalog/products/?brand_id=3&product_type=decant&min_price=200&max_price=800
    """
    serializer_class = ProductListSerializer
    pagination_class = ProductListPagination

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=1)
            .select_related('perfume', 'perfume__brand')
        )

        brand_id = self.request.query_params.get('brand_id') or self.request.query_params.get('brand')
        if brand_id:
            queryset = queryset.filter(perfume__brand_id=brand_id)

        size = self.request.query_params.get('size')
        if size:
            queryset = queryset.filter(volume_ml=size)

        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type__iexact=product_type)

        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset.order_by('perfume__perfume_name', 'volume_ml')


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET /api/catalog/products/<product_id>/

    Returns full detail for a single product: brand, notes, price,
    and the rest of the perfume info, in one request.
    """
    queryset = Product.objects.select_related('perfume', 'perfume__brand').all()
    serializer_class = ProductDetailSerializer
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'
