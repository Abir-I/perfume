"""
Server-rendered Product Details page.

One template serves every product on the site (Home, Shop, Brands, Search,
Wishlist, Related Products…) resolved by slug and/or ID.
"""

from django.http import Http404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import redirect, render

from .detail_utils import (
    detail_payload,
    product_url,
    push_recently_viewed,
    recently_viewed,
    related_products,
    resolve_product,
    review_payload,
    wishlist_ids,
)
from accounts.models import Review


@ensure_csrf_cookie
def product_detail_page(request, product_id=None, slug=None):
    product = resolve_product(product_id=product_id, slug=slug)
    if not product:
        raise Http404('Product not found')

    canonical = product_url(product)
    if request.path != canonical:
        return redirect(canonical, permanent=False)

    push_recently_viewed(request, product.product_id)

    data = detail_payload(product, request)
    reviews = (
        Review.objects.select_related('user')
        .filter(product__perfume=product.perfume)
        .order_by('-created_at')[:20]
    )

    context = {
        'product': data,
        'reviews': [review_payload(r) for r in reviews],
        'related': related_products(product),
        'recently': recently_viewed(request, exclude_id=product.product_id),
        'in_wishlist': product.product_id in wishlist_ids(request),
    }
    return render(request, 'product_detail.html', context)


def product_detail_redirect(request):
    """Legacy /products/?id=<id> entry point → canonical detail URL."""
    raw_id = request.GET.get('id') or request.GET.get('product_id')
    slug = request.GET.get('slug')
    product = resolve_product(
        product_id=int(raw_id) if (raw_id or '').isdigit() else None,
        slug=slug,
    )
    if product:
        return redirect(product_url(product))
    return redirect('/shop/')
