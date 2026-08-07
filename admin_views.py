import os
import uuid

from django.conf import settings
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Perfume, Product

from .admin_serializers import (
    PerfumeWriteSerializer,
    ProductImageUploadSerializer,
    ProductVariantWriteSerializer,
)
from .permissions import IsAdminRole
from .serializers import ProductSerializer, PerfumeSerializer


def _perfume_admin_data(perfume):
    """
    PerfumeSerializer (catalog/serializers.py) doesn't include `sillage`
    or `description` — they're not needed for browsing, but the admin
    panel needs to see/edit them. Adding them here rather than editing
    the shared serializer, so nothing else that uses it is affected.
    """
    data = PerfumeSerializer(perfume).data
    data['sillage'] = perfume.sillage
    data['description'] = perfume.description
    return data


class AdminAuthMixin:
    """Shared auth for every admin endpoint in this file: valid JWT + admin role."""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]


class AdminPerfumeCreateView(AdminAuthMixin, APIView):
    """POST /api/admin/catalog/perfumes/ — add a new perfume."""

    def post(self, request):
        serializer = PerfumeWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        perfume = Perfume.objects.create(
            brand=serializer.get_brand(),
            perfume_name=data['perfume_name'],
            concentration=data['concentration'],
            top_notes=data['top_notes'],
            middle_notes=data['middle_notes'],
            base_notes=data['base_notes'],
            longevity_hours=data['longevity_hours'],
            sillage=data['sillage'],
            recommended_season=data['recommended_season'],
            target_gender=data['target_gender'],
            description=data['description'],
            created_at=timezone.now(),
        )
        return Response(_perfume_admin_data(perfume), status=status.HTTP_201_CREATED)


class AdminPerfumeDetailView(AdminAuthMixin, APIView):
    """
    PUT    /api/admin/catalog/perfumes/<perfume_id>/  — edit a perfume
    DELETE /api/admin/catalog/perfumes/<perfume_id>/  — deactivate a perfume

    Deleting doesn't drop the row — orders, reviews, and decant batches
    may reference it. Instead every product variant under this perfume
    gets deactivated (is_active=0), which is exactly what the customer
    browsing endpoint filters on, so it disappears from the shop
    immediately without touching order history.
    """

    def get(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)
        return Response(_perfume_admin_data(perfume), status=status.HTTP_200_OK)

    def put(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)
        serializer = PerfumeWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        perfume.brand = serializer.get_brand()
        perfume.perfume_name = data['perfume_name']
        perfume.concentration = data['concentration']
        perfume.top_notes = data['top_notes']
        perfume.middle_notes = data['middle_notes']
        perfume.base_notes = data['base_notes']
        perfume.longevity_hours = data['longevity_hours']
        perfume.sillage = data['sillage']
        perfume.recommended_season = data['recommended_season']
        perfume.target_gender = data['target_gender']
        perfume.description = data['description']
        perfume.save()

        return Response(_perfume_admin_data(perfume), status=status.HTTP_200_OK)

    def delete(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)
        deactivated = Product.objects.filter(perfume=perfume).update(is_active=0)
        return Response(
            {
                "message": "Perfume deactivated.",
                "perfume_id": perfume.perfume_id,
                "variants_deactivated": deactivated,
            },
            status=status.HTTP_200_OK,
        )


class AdminVariantCreateView(AdminAuthMixin, APIView):
    """POST /api/admin/catalog/perfumes/<perfume_id>/variants/ — add a size/price variant."""

    def post(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)
        serializer = ProductVariantWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product = Product.objects.create(
            perfume=perfume,
            product_type=data['product_type'],
            volume_ml=data['volume_ml'],
            price=data['price'],
            stock_quantity=data['stock_quantity'],
            is_active=1 if data['is_active'] else 0,
            created_at=timezone.now(),
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class AdminVariantDetailView(AdminAuthMixin, APIView):
    """
    PUT    /api/admin/catalog/products/<product_id>/  — edit a variant (price/stock/type)
    DELETE /api/admin/catalog/products/<product_id>/  — deactivate a variant
    """

    def put(self, request, product_id):
        product = get_object_or_404(Product, product_id=product_id)
        serializer = ProductVariantWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product.product_type = data['product_type']
        product.volume_ml = data['volume_ml']
        product.price = data['price']
        product.stock_quantity = data['stock_quantity']
        product.is_active = 1 if data['is_active'] else 0
        product.save()

        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)

    def delete(self, request, product_id):
        product = get_object_or_404(Product, product_id=product_id)
        product.is_active = 0
        product.save(update_fields=['is_active'])
        return Response(
            {"message": "Variant deactivated.", "product_id": product.product_id},
            status=status.HTTP_200_OK,
        )


class AdminImageUploadView(AdminAuthMixin, APIView):
    """
    POST /api/admin/catalog/perfumes/<perfume_id>/image/

    multipart/form-data with a single `image` field (JPG or PNG, <=5MB).
    Saves to static/images/products/, deletes the perfume's previous
    image if it was one of ours, and stores the new URL on the row.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)

        serializer = ProductImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        image = serializer.validated_data['image']

        static_root = settings.STATICFILES_DIRS[0]
        products_dir = os.path.join(static_root, 'images', 'products')
        os.makedirs(products_dir, exist_ok=True)

        ext = os.path.splitext(image.name)[1].lower()
        filename = f"perfume_{perfume.perfume_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(products_dir, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        old_url = perfume.image_url
        if old_url and old_url.startswith(f"{settings.STATIC_URL}images/products/"):
            old_relative = old_url[len(settings.STATIC_URL):]
            old_path = os.path.join(static_root, old_relative)
            if os.path.isfile(old_path) and old_path != file_path:
                os.remove(old_path)

        new_url = f"{settings.STATIC_URL}images/products/{filename}"
        perfume.image_url = new_url
        perfume.save(update_fields=['image_url'])

        return Response({"image_url": new_url}, status=status.HTTP_201_CREATED)


class AdminInventoryView(AdminAuthMixin, APIView):
    """
    GET /api/admin/catalog/inventory/?low_stock_threshold=5

    Lists stock levels for every product and flags anything at or below
    the threshold (default 5).
    """

    def get(self, request):
        try:
            threshold = int(request.query_params.get('low_stock_threshold', 5))
        except (TypeError, ValueError):
            threshold = 5

        products = Product.objects.select_related('perfume', 'perfume__brand').order_by('stock_quantity')

        results = []
        low_stock_count = 0
        for p in products:
            is_low = p.stock_quantity <= threshold
            if is_low:
                low_stock_count += 1
            results.append({
                "product_id": p.product_id,
                "perfume_id": p.perfume.perfume_id,
                "perfume_name": p.perfume.perfume_name,
                "brand_name": p.perfume.brand.brand_name,
                "product_type": p.product_type,
                "volume_ml": p.volume_ml,
                "stock_quantity": p.stock_quantity,
                "is_active": bool(p.is_active),
                "low_stock": is_low,
            })

        return Response({
            "count": len(results),
            "low_stock_threshold": threshold,
            "low_stock_count": low_stock_count,
            "results": results,
        }, status=status.HTTP_200_OK)


class AdminSearchView(AdminAuthMixin, APIView):
    """
    GET /api/admin/catalog/search/?q=dior

    Search by perfume name, brand name, or concentration, for the admin
    dashboard's search bar. Returns total stock per perfume too.
    """

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        perfumes = Perfume.objects.select_related('brand').annotate(
            current_stock=Sum('product__stock_quantity')
        )
        if q:
            perfumes = perfumes.filter(
                Q(perfume_name__icontains=q)
                | Q(brand__brand_name__icontains=q)
                | Q(concentration__icontains=q)
            )
        perfumes = perfumes.order_by('perfume_name')

        results = [
            {
                "perfume_id": p.perfume_id,
                "perfume_name": p.perfume_name,
                "brand_name": p.brand.brand_name,
                "concentration": p.concentration,
                "current_stock": p.current_stock or 0,
            }
            for p in perfumes
        ]
        return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)
