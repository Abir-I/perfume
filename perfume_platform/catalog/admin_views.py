"""
Admin-only catalog management views: list every product (including
out-of-stock/inactive), create a perfume + its first product variant,
edit both, and delete a product. Powers the admin dashboard frontend.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from accounts.authentication import CustomJWTAuthentication
from accounts.permissions import IsAdminRole
from accounts.models import Brand, Perfume, Product
from .serializers import ProductSerializer

VALID_CONCENTRATIONS = {'EDT', 'EDP', 'Parfum', 'EDC', 'Cologne'}
MAX_CONCENTRATION_LENGTH = 50
MAX_SEASON_LENGTH = 100
VALID_GENDERS = {'Male', 'Female', 'Unisex'}
VALID_PRODUCT_TYPES = {'full_bottle', 'decant'}
VALID_SEASONS = {'Spring', 'Summer', 'Fall', 'Winter', 'All Season'}


def _save_uploaded_image(image_file):
    """Save an uploaded image file to MEDIA_ROOT and return its public URL."""
    from django.core.files.storage import default_storage
    path = default_storage.save(f'perfumes/{image_file.name}', image_file)
    return default_storage.url(path)


class AdminProductListView(APIView):
    """
    GET /api/catalog/admin/products/
    Returns every product for the admin dashboard table — including
    out-of-stock and deactivated ones, unlike the public product list.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        products = Product.objects.select_related('perfume', 'perfume__brand').all().order_by('-created_at')

        search = request.query_params.get('search', '').strip()
        if search:
            products = products.filter(perfume__perfume_name__icontains=search)

        serializer = ProductSerializer(products, many=True)
        return Response({
            'count': products.count(),
            'results': serializer.data,
        }, status=status.HTTP_200_OK)


class AdminPerfumeCreateView(APIView):
    """
    POST /api/catalog/admin/perfumes/
    Creates a new perfume plus its first product variant in one call.
    Accepts multipart/form-data so an image file can be uploaded
    alongside the text fields; falls back to plain JSON if no file.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = request.data

        # ---- Required perfume fields ----
        brand_id = data.get('brand_id')
        perfume_name = (data.get('perfume_name') or '').strip()
        concentration = data.get('concentration')
        target_gender = data.get('target_gender')

        errors = {}
        if not brand_id:
            errors['brand_id'] = 'Brand is required.'
        if not perfume_name:
            errors['perfume_name'] = 'Perfume name is required.'
        concentration = (str(concentration).strip() if concentration is not None else '')
        if not concentration:
            errors['concentration'] = 'Concentration is required.'
        elif len(concentration) > MAX_CONCENTRATION_LENGTH:
            errors['concentration'] = f'Concentration must be {MAX_CONCENTRATION_LENGTH} characters or fewer.'
        if target_gender not in VALID_GENDERS:
            errors['target_gender'] = f'Must be one of {sorted(VALID_GENDERS)}.'

        # ---- Required initial product variant fields ----
        product_type = data.get('product_type')
        volume_ml = data.get('volume_ml')
        price = data.get('price')
        if product_type not in VALID_PRODUCT_TYPES:
            errors['product_type'] = f'Must be one of {sorted(VALID_PRODUCT_TYPES)}.'
        if not volume_ml:
            errors['volume_ml'] = 'Volume (ml) is required.'
        if not price:
            errors['price'] = 'Price is required.'

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            brand = Brand.objects.get(brand_id=brand_id)
        except Brand.DoesNotExist:
            return Response({'errors': {'brand_id': 'Brand not found.'}}, status=status.HTTP_404_NOT_FOUND)

        recommended_season = (str(data.get('recommended_season')).strip() if data.get('recommended_season') else None)
        if recommended_season and len(recommended_season) > MAX_SEASON_LENGTH:
            return Response({'errors': {'recommended_season': f'Recommended season must be {MAX_SEASON_LENGTH} characters or fewer.'}},
                             status=status.HTTP_400_BAD_REQUEST)

        image_url = None
        image_file = request.FILES.get('image')
        if image_file:
            image_url = _save_uploaded_image(image_file)
        elif data.get('image_url'):
            image_url = data.get('image_url')

        try:
            price_val = float(price)
            volume_val = float(volume_ml)
            stock_val = int(data.get('stock_quantity') or 0)
            if price_val <= 0:
                return Response({'errors': {'price': 'Price must be greater than 0.'}}, status=status.HTTP_400_BAD_REQUEST)
            if stock_val < 0:
                return Response({'errors': {'stock_quantity': 'Stock cannot be negative.'}}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'errors': {'price': 'Price and volume must be numbers.'}}, status=status.HTTP_400_BAD_REQUEST)

        perfume = Perfume.objects.create(
            brand=brand,
            perfume_name=perfume_name,
            concentration=concentration,
            top_notes=data.get('top_notes') or None,
            middle_notes=data.get('middle_notes') or None,
            base_notes=data.get('base_notes') or None,
            longevity_hours=data.get('longevity_hours') or None,
            sillage=data.get('sillage') or None,
            recommended_season=recommended_season,
            target_gender=target_gender,
            description=data.get('description') or None,
            image_url=image_url,
            created_at=timezone.now(),
        )

        product = Product.objects.create(
            perfume=perfume,
            product_type=product_type,
            volume_ml=volume_val,
            price=price_val,
            stock_quantity=stock_val,
            is_active=1,
            created_at=timezone.now(),
        )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminPerfumeUpdateView(APIView):
    """
    PATCH /api/catalog/admin/perfumes/<perfume_id>/
    Edits perfume fields (brand, name, notes, gender, longevity, etc).
    Optionally updates one product variant's price/stock/volume/type
    at the same time if `product_id` is included in the payload —
    the admin edit form submits perfume + its variant together.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, perfume_id):
        try:
            perfume = Perfume.objects.get(perfume_id=perfume_id)
        except Perfume.DoesNotExist:
            return Response({'error': 'Perfume not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        if 'brand_id' in data and data.get('brand_id'):
            try:
                perfume.brand = Brand.objects.get(brand_id=data['brand_id'])
            except Brand.DoesNotExist:
                return Response({'errors': {'brand_id': 'Brand not found.'}}, status=status.HTTP_404_NOT_FOUND)

        if data.get('perfume_name'):
            perfume.perfume_name = data['perfume_name'].strip()

        if 'concentration' in data:
            concentration_value = str(data.get('concentration') or '').strip()
            if not concentration_value:
                return Response({'errors': {'concentration': 'Concentration is required.'}},
                                 status=status.HTTP_400_BAD_REQUEST)
            if len(concentration_value) > MAX_CONCENTRATION_LENGTH:
                return Response({'errors': {'concentration': f'Concentration must be {MAX_CONCENTRATION_LENGTH} characters or fewer.'}},
                                 status=status.HTTP_400_BAD_REQUEST)
            perfume.concentration = concentration_value

        if data.get('target_gender'):
            if data['target_gender'] not in VALID_GENDERS:
                return Response({'errors': {'target_gender': f'Must be one of {sorted(VALID_GENDERS)}.'}},
                                 status=status.HTTP_400_BAD_REQUEST)
            perfume.target_gender = data['target_gender']

        if 'recommended_season' in data:
            season_value = str(data.get('recommended_season') or '').strip()
            if len(season_value) > MAX_SEASON_LENGTH:
                return Response({'errors': {'recommended_season': f'Recommended season must be {MAX_SEASON_LENGTH} characters or fewer.'}},
                                 status=status.HTTP_400_BAD_REQUEST)
            perfume.recommended_season = season_value or None

        for field in ('top_notes', 'middle_notes', 'base_notes', 'sillage', 'description', 'longevity_hours'):
            if field in data:
                setattr(perfume, field, data.get(field) or None)

        image_file = request.FILES.get('image')
        if image_file:
            perfume.image_url = _save_uploaded_image(image_file)
        elif data.get('image_url'):
            perfume.image_url = data.get('image_url')

        perfume.save()

        # Optionally update the linked product variant in the same request
        product = None
        product_id = data.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(product_id=product_id, perfume=perfume)
            except Product.DoesNotExist:
                return Response({'errors': {'product_id': 'Product variant not found for this perfume.'}},
                                 status=status.HTTP_404_NOT_FOUND)

            try:
                if data.get('price'):
                    price_val = float(data['price'])
                    if price_val <= 0:
                        return Response({'errors': {'price': 'Price must be greater than 0.'}}, status=status.HTTP_400_BAD_REQUEST)
                    product.price = price_val
                if data.get('volume_ml'):
                    product.volume_ml = float(data['volume_ml'])
                if data.get('stock_quantity') is not None and data.get('stock_quantity') != '':
                    stock_val = int(data['stock_quantity'])
                    if stock_val < 0:
                        return Response({'errors': {'stock_quantity': 'Stock cannot be negative.'}}, status=status.HTTP_400_BAD_REQUEST)
                    product.stock_quantity = stock_val
                if data.get('product_type'):
                    if data['product_type'] not in VALID_PRODUCT_TYPES:
                        return Response({'errors': {'product_type': f'Must be one of {sorted(VALID_PRODUCT_TYPES)}.'}},
                                         status=status.HTTP_400_BAD_REQUEST)
                    product.product_type = data['product_type']
                if 'is_active' in data:
                    product.is_active = 1 if str(data['is_active']) in ('1', 'true', 'True') else 0
            except (TypeError, ValueError):
                return Response({'errors': {'price': 'Price, volume, and stock must be numbers.'}}, status=status.HTTP_400_BAD_REQUEST)

            product.save()

        serializer = ProductSerializer(product) if product else None
        return Response({
            'perfume_id': perfume.perfume_id,
            'perfume_name': perfume.perfume_name,
            'image_url': perfume.image_url,
            'product': serializer.data if serializer else None,
        }, status=status.HTTP_200_OK)


class AdminProductDeleteView(APIView):
    """
    DELETE /api/catalog/admin/products/<product_id>/
    Removes a single product variant (e.g. discontinuing a size), not
    the whole perfume — a perfume can have several variants (5ml, 10ml,
    full bottle) and deleting one shouldn't remove the others.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminRole]

    def delete(self, request, product_id):
        from django.db.utils import IntegrityError

        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            product.delete()
        except IntegrityError:
            # This product is referenced by an existing order or cart —
            # deleting it would orphan that history. Deactivate instead
            # so it disappears from the shop without breaking past orders.
            product.is_active = 0
            product.save(update_fields=['is_active'])
            return Response({
                'message': 'This product has existing orders and can\'t be permanently deleted — '
                           'it has been deactivated and removed from the shop instead.',
            }, status=status.HTTP_200_OK)

        return Response({'message': 'Product deleted.'}, status=status.HTTP_200_OK)
