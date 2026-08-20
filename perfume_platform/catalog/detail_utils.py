"""
Shared helpers for the dynamic Product Details page.

Everything here works against the EXISTING database models
(accounts.models: Brand, Perfume, Product, Review) — no new tables,
no duplicated product models.
"""

import re
from decimal import Decimal

from django.db.models import Avg, Count, Q

from .serializers import normalize_image_url
from accounts.models import Perfume, Product, Review


FALLBACK_IMAGE = (
    'https://images.unsplash.com/photo-1541643600914-78b084683702'
    '?w=900&q=80&auto=format'
)

# Secondary angles used only when a perfume has a single stored image, so the
# gallery / zoom viewer always has something to switch between.
SECONDARY_IMAGES = [
    'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=900&q=80&auto=format',
    'https://images.unsplash.com/photo-1599305090598-fe179d501227?w=900&q=80&auto=format',
    'https://images.unsplash.com/photo-1595425970377-c9703cf48b6d?w=900&q=80&auto=format',
]


def slugify_name(value):
    """URL-friendly slug built from the perfume + brand name."""
    value = (value or '').strip().lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-') or 'product'


def product_slug(product):
    return slugify_name(
        f"{product.perfume.brand.brand_name} {product.perfume.perfume_name}"
    )


def product_url(product):
    return f"/product/{product_slug(product)}/{product.product_id}/"


def split_notes(raw):
    """'Bergamot, Pepper · Cedar' -> ['Bergamot', 'Pepper', 'Cedar']"""
    if not raw:
        return []
    parts = re.split(r'[,·/|]+', str(raw))
    return [p.strip() for p in parts if p.strip()]


def stock_state(product):
    qty = product.stock_quantity or 0
    if qty <= 0:
        return 'out_of_stock', 'Out of Stock'
    if qty <= 5:
        return 'low_stock', f'Only {qty} left'
    return 'in_stock', 'In Stock'


def _float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def gallery_for(perfume):
    main = normalize_image_url(perfume.image_url) or FALLBACK_IMAGE
    images = [main]
    for extra in SECONDARY_IMAGES:
        if extra != main and len(images) < 4:
            images.append(extra)
    return images


def rating_summary(product):
    """Aggregate rating for the product, falling back to the whole perfume."""
    agg = Review.objects.filter(product=product).aggregate(
        avg=Avg('rating'), total=Count('review_id')
    )
    if not agg['total']:
        agg = Review.objects.filter(product__perfume=product.perfume).aggregate(
            avg=Avg('rating'), total=Count('review_id')
        )

    breakdown = {str(i): 0 for i in range(1, 6)}
    rows = (
        Review.objects.filter(product__perfume=product.perfume)
        .values('rating')
        .annotate(n=Count('review_id'))
    )
    for row in rows:
        breakdown[str(row['rating'])] = row['n']

    return {
        'average': round(float(agg['avg'] or 0), 1),
        'count': agg['total'] or 0,
        'breakdown': breakdown,
    }


def review_payload(review):
    user = review.user
    name = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return {
        'review_id': review.review_id,
        'rating': review.rating,
        'comment': review.comment or '',
        'user_name': name or 'Verified Customer',
        'is_verified_purchase': bool(review.is_verified_purchase),
        'created_at': review.created_at.isoformat() if review.created_at else None,
        'created_display': review.created_at.strftime('%d %b %Y') if review.created_at else '',
    }


def card_payload(product):
    """Compact payload used by related / recently-viewed / variant cards."""
    perfume = product.perfume
    return {
        'product_id': product.product_id,
        'perfume_id': perfume.perfume_id,
        'perfume_name': perfume.perfume_name,
        'brand_id': perfume.brand_id,
        'brand_name': perfume.brand.brand_name,
        'concentration': perfume.concentration,
        'product_type': product.product_type,
        'volume_ml': _float(product.volume_ml),
        'price': _float(product.price),
        'stock_quantity': product.stock_quantity,
        'image_url': normalize_image_url(perfume.image_url) or FALLBACK_IMAGE,
        'url': product_url(product),
    }


def detail_payload(product, request=None):
    """Full payload backing the Product Details page."""
    perfume = product.perfume
    brand = perfume.brand
    state, state_label = stock_state(product)

    variants = (
        Product.objects.select_related('perfume', 'perfume__brand')
        .filter(perfume=perfume, is_active=1)
        .order_by('volume_ml')
    )

    specs = [
        ('Brand', brand.brand_name),
        ('Concentration', perfume.concentration),
        ('Volume', f"{_float(product.volume_ml):g} ml" if product.volume_ml else '—'),
        ('Type', 'Decant' if product.product_type == 'decant' else 'Full Bottle'),
        ('Gender', perfume.target_gender or '—'),
        ('Season', perfume.recommended_season or '—'),
        ('Longevity', f"{_float(perfume.longevity_hours):g} hours" if perfume.longevity_hours else '—'),
        ('Sillage', perfume.sillage or '—'),
        ('Origin', brand.country_of_origin or '—'),
    ]

    return {
        'product_id': product.product_id,
        'slug': product_slug(product),
        'url': product_url(product),
        'perfume_id': perfume.perfume_id,
        'perfume_name': perfume.perfume_name,
        'brand': {
            'brand_id': brand.brand_id,
            'brand_name': brand.brand_name,
            'country_of_origin': brand.country_of_origin or '',
            'description': brand.description or '',
        },
        'category': 'Decant' if product.product_type == 'decant' else 'Full Bottle',
        'sub_category': perfume.concentration,
        'description': perfume.description or '',
        'price': _float(product.price),
        'volume_ml': _float(product.volume_ml),
        'product_type': product.product_type,
        'stock_quantity': product.stock_quantity,
        'stock_state': state,
        'stock_label': state_label,
        'images': gallery_for(perfume),
        'notes': {
            'top': split_notes(perfume.top_notes),
            'middle': split_notes(perfume.middle_notes),
            'base': split_notes(perfume.base_notes),
        },
        'specs': [{'label': k, 'value': v} for k, v in specs],
        'rating': rating_summary(product),
        'variants': [card_payload(v) for v in variants],
    }


def related_products(product, limit=8):
    """Same brand, category (product type) or overlapping fragrance notes."""
    perfume = product.perfume
    note_terms = []
    for raw in (perfume.top_notes, perfume.middle_notes, perfume.base_notes):
        note_terms.extend(split_notes(raw))
    note_terms = note_terms[:6]

    note_q = Q()
    for term in note_terms:
        note_q |= Q(perfume__top_notes__icontains=term)
        note_q |= Q(perfume__middle_notes__icontains=term)
        note_q |= Q(perfume__base_notes__icontains=term)

    query = (
        Q(perfume__brand_id=perfume.brand_id)
        | Q(product_type=product.product_type)
        | Q(perfume__concentration=perfume.concentration)
        | note_q
    )

    qs = (
        Product.objects.select_related('perfume', 'perfume__brand')
        .filter(is_active=1)
        .filter(query)
        .exclude(product_id=product.product_id)
        .exclude(perfume_id=perfume.perfume_id)
        .distinct()
    )

    # Brand matches first, then everything else.
    same_brand = [p for p in qs if p.perfume.brand_id == perfume.brand_id]
    others = [p for p in qs if p.perfume.brand_id != perfume.brand_id]
    ordered = (same_brand + others)[:limit]

    if len(ordered) < limit:
        filler = (
            Product.objects.select_related('perfume', 'perfume__brand')
            .filter(is_active=1)
            .exclude(product_id=product.product_id)
            .exclude(product_id__in=[p.product_id for p in ordered])
            .order_by('-product_id')[: limit - len(ordered)]
        )
        ordered += list(filler)

    return [card_payload(p) for p in ordered]


def get_product_or_none(product_id):
    return (
        Product.objects.select_related('perfume', 'perfume__brand')
        .filter(product_id=product_id)
        .first()
    )


def resolve_product(product_id=None, slug=None):
    """Resolve a product by ID first, then by slug (brand-name-perfume-name)."""
    if product_id:
        product = get_product_or_none(product_id)
        if product:
            return product

    if slug:
        slug = slug.lower()
        candidates = Product.objects.select_related(
            'perfume', 'perfume__brand'
        ).filter(is_active=1)
        for product in candidates:
            if product_slug(product) == slug:
                return product
        # Also allow a perfume-level slug (any active variant of that perfume)
        for perfume in Perfume.objects.select_related('brand'):
            if slugify_name(perfume.perfume_name) == slug:
                return (
                    Product.objects.select_related('perfume', 'perfume__brand')
                    .filter(perfume=perfume, is_active=1)
                    .order_by('volume_ml')
                    .first()
                )
    return None


# ── Session-backed lists (wishlist / recently viewed) ────────────────────
RECENT_KEY = 'recently_viewed_products'
WISHLIST_KEY = 'wishlist_products'
GUEST_CART_KEY = 'guest_cart'
RECENT_LIMIT = 12


def push_recently_viewed(request, product_id):
    ids = [i for i in request.session.get(RECENT_KEY, []) if i != product_id]
    ids.insert(0, product_id)
    request.session[RECENT_KEY] = ids[:RECENT_LIMIT]
    request.session.modified = True


def recently_viewed(request, exclude_id=None, limit=8):
    ids = [i for i in request.session.get(RECENT_KEY, []) if i != exclude_id]
    if not ids:
        return []
    products = {
        p.product_id: p
        for p in Product.objects.select_related('perfume', 'perfume__brand').filter(
            product_id__in=ids
        )
    }
    return [card_payload(products[i]) for i in ids if i in products][:limit]


def wishlist_ids(request):
    return list(request.session.get(WISHLIST_KEY, []))


def toggle_wishlist(request, product_id):
    ids = wishlist_ids(request)
    if product_id in ids:
        ids.remove(product_id)
        in_wishlist = False
    else:
        ids.insert(0, product_id)
        in_wishlist = True
    request.session[WISHLIST_KEY] = ids
    request.session.modified = True
    return in_wishlist


def wishlist_products(request):
    ids = wishlist_ids(request)
    if not ids:
        return []
    products = {
        p.product_id: p
        for p in Product.objects.select_related('perfume', 'perfume__brand').filter(
            product_id__in=ids
        )
    }
    return [card_payload(products[i]) for i in ids if i in products]
