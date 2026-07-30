import os
import uuid

from django.conf import settings
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, mixins, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfume, Product
from .admin_serializers import (
    AdminSearchResultSerializer,
    PerfumeAdminSerializer,
    ProductImageUploadSerializer,
    ProductVariantAdminSerializer,
)
from .permissions import IsAdminRole


class AdminAPIViewMixin:
    """
    settings.py sets JWTAuthentication as the project-wide
    DEFAULT_AUTHENTICATION_CLASSES, but its get_user() resolves the
    token's user_id against django.contrib.auth's built-in User model
    (the `auth_user` table) — not accounts.User, which is what the
    tokens are actually built from in accounts/views.py:LoginView. Any
    DRF view that touches request.user (which happens automatically)
    throws a DB error the moment a Bearer token is sent, before
    permissions are even checked. This is a pre-existing issue on the
    `Abir` branch, unrelated to catalog.

    We sidestep it here by not authenticating at the DRF layer at all —
    IsAdminRole already decodes and checks the JWT itself, so we don't
    need request.user for these endpoints. accounts/ still needs a real
    fix for this (either set AUTH_USER_MODEL = 'accounts.User', or swap
    to a custom JWTAuthentication subclass that looks users up in
    accounts.User).
    """
    authentication_classes = []


class PerfumeAdminCreateView(AdminAPIViewMixin, generics.CreateAPIView):
    """POST /api/admin/catalog/perfumes/ — add a new perfume."""
    queryset = Perfume.objects.all()
    serializer_class = PerfumeAdminSerializer
    permission_classes = [IsAdminRole]

    def perform_create(self, serializer):
        serializer.save(created_at=timezone.now())


class PerfumeAdminDetailView(AdminAPIViewMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    """
    PUT    /api/admin/catalog/perfumes/<perfume_id>/  — edit a perfume
    DELETE /api/admin/catalog/perfumes/<perfume_id>/  — deactivate a perfume

    Deleting doesn't drop the row — orders, reviews, and decant batches
    may reference it, and hard-deleting could break that history. Instead
    we deactivate every product variant under this perfume, which is
    exactly what the customer-facing browsing endpoint filters on
    (`is_active=1`), so it disappears from the shop immediately.
    """
    queryset = Perfume.objects.all()
    serializer_class = PerfumeAdminSerializer
    permission_classes = [IsAdminRole]
    lookup_field = 'perfume_id'
    lookup_url_kwarg = 'perfume_id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        perfume = self.get_object()
        deactivated = Product.objects.filter(perfume=perfume).update(is_active=0)
        return Response(
            {
                "message": "Perfume deactivated.",
                "perfume_id": perfume.perfume_id,
                "variants_deactivated": deactivated,
            },
            status=status.HTTP_200_OK,
        )


class ProductVariantCreateView(AdminAPIViewMixin, generics.CreateAPIView):
    """
    POST /api/admin/catalog/perfumes/<perfume_id>/variants/

    Add a size/price variant (a Product row) under an existing perfume.
    """
    serializer_class = ProductVariantAdminSerializer
    permission_classes = [IsAdminRole]

    def perform_create(self, serializer):
        perfume = get_object_or_404(Perfume, perfume_id=self.kwargs['perfume_id'])
        serializer.save(perfume=perfume, is_active=1, created_at=timezone.now())


class ProductVariantDetailView(AdminAPIViewMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    """
    PUT    /api/admin/catalog/products/<product_id>/  — edit a variant (price/stock/type)
    DELETE /api/admin/catalog/products/<product_id>/  — deactivate a variant
    """
    queryset = Product.objects.all()
    serializer_class = ProductVariantAdminSerializer
    permission_classes = [IsAdminRole]
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        product.is_active = 0
        product.save(update_fields=['is_active'])
        return Response(
            {"message": "Variant deactivated.", "product_id": product.product_id},
            status=status.HTTP_200_OK,
        )


class ProductImageUploadView(AdminAPIViewMixin, APIView):
    """
    POST /api/admin/catalog/perfumes/<perfume_id>/image/

    multipart/form-data with a single `image` field (JPG or PNG, <=5MB).
    Saves the file under static/images/products/, deletes the perfume's
    previous image if it was one of ours, and stores the new URL on the
    Perfume row.
    """
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, perfume_id):
        perfume = get_object_or_404(Perfume, perfume_id=perfume_id)

        serializer = ProductImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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

        # remove the old file if it lives in our own products folder
        # (skip anything that looks like an external/hotlinked URL)
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


class AdminProductSearchView(AdminAPIViewMixin, generics.ListAPIView):
    """
    GET /api/admin/catalog/search/?q=dior

    Search by perfume name, brand name, or concentration. Returns one
    row per perfume with brand + total stock across its variants, for
    the admin dashboard's search bar.
    """
    serializer_class = AdminSearchResultSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()
        queryset = Perfume.objects.select_related('brand').annotate(
            current_stock=Sum('product__stock_quantity')
        )
        if q:
            queryset = queryset.filter(
                Q(perfume_name__icontains=q)
                | Q(brand__brand_name__icontains=q)
                | Q(concentration__icontains=q)
            )
        return queryset.order_by('perfume_name')
