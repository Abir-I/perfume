/* ══════════════════════════════════════════════════════════════
   THE LAST NOTE · product-links.js
   Shared storefront helpers — one Product Details page for every
   product across Home, Shop, Brands, Search, Wishlist and rails.
   Loaded AFTER script.js (which defines API_BASE / showToast).
   ══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* Always same-origin: the storefront APIs are served by this Django app. */
  const API = '/api';

  /* ── utils ── */
  function slugify(text) {
    return String(text || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'product';
  }

  function productUrl(product) {
    if (!product) return '/shop/';
    if (product.url) return product.url;
    const id = product.product_id || product.id;
    if (!id) return '/shop/';
    const slug = slugify(`${product.brand_name || product.brand || ''} ${product.perfume_name || product.name || ''}`);
    return `/product/${slug}/${id}/`;
  }

  function goToProduct(product) {
    window.location.href = productUrl(product);
  }

  function toast(msg) {
    if (typeof window.showToast === 'function') { window.showToast(msg); return; }
    let el = document.getElementById('pdToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'pdToast';
      el.className = 'pd-toast';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add('on');
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('on'), 2600);
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : '';
  }

  function headers() {
    const h = { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') };
    const token = localStorage.getItem('access_token');
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  }

  async function post(path, body) {
    const res = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: headers(),
      credentials: 'same-origin',
      body: JSON.stringify(body || {}),
    });
    let data = {};
    try { data = await res.json(); } catch (_) {}
    if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'), { data, status: res.status });
    return data;
  }

  async function get(path) {
    const res = await fetch(`${API}${path}`, { headers: headers(), credentials: 'same-origin' });
    return res.json();
  }

  /* ── cart ── */
  function setCartBadge(count) {
    document.querySelectorAll('#cartBadge, .cart-badge').forEach(el => {
      el.textContent = count;
      el.style.display = count > 0 ? '' : el.style.display;
    });
    if (typeof window.cartItems !== 'undefined') window.cartItems = count;
  }

  async function refreshCartBadge() {
    try {
      const data = await get('/cart/');
      setCartBadge(data.total_items || 0);
      return data;
    } catch (_) { return null; }
  }

  async function addToCart(productId, quantity) {
    const data = await post('/cart/add/', {
      product_id: productId,
      quantity: quantity || 1,
    });
    setCartBadge(data.total_items || 0);
    return data;
  }

  /* ── wishlist ── */
  async function toggleWishlist(productId) {
    return post('/catalog/wishlist/', { product_id: productId });
  }

  async function getWishlist() { return get('/catalog/wishlist/'); }

  /* ── recently viewed ── */
  async function recordView(productId) {
    try { await post('/catalog/recently-viewed/', { product_id: productId }); } catch (_) {}
  }
  async function getRecentlyViewed(excludeId) {
    return get(`/catalog/recently-viewed/${excludeId ? '?exclude=' + excludeId : ''}`);
  }

  /* ── make every product card open the detail page ── */
  document.addEventListener('click', function (event) {
    const actionBtn = event.target.closest('button, a[href], input, select, textarea, [data-no-nav]');
    const card = event.target.closest('[data-product-id]');
    if (!card) return;
    // Let real buttons/links inside a card do their own job.
    if (actionBtn && actionBtn !== card && card.contains(actionBtn)) return;
    if (card.tagName === 'A' && card.getAttribute('href')) return;

    const id = card.getAttribute('data-product-id');
    if (!id) return;
    event.preventDefault();
    window.location.href = productUrl({
      product_id: id,
      perfume_name: card.getAttribute('data-perfume-name') || '',
      brand_name: card.getAttribute('data-brand-name') || '',
    });
  });

  /* ── Quick View now opens the real Product Details page ── */
  const legacyQuickView = window.quickView;
  window.quickView = function (nameOrProduct, brand, productId) {
    if (nameOrProduct && typeof nameOrProduct === 'object') return goToProduct(nameOrProduct);
    if (productId) return goToProduct({ product_id: productId, perfume_name: nameOrProduct, brand_name: brand });

    // Fall back to a name/brand search so the click still lands on the right page.
    fetch(`${API}/catalog/products/?search=${encodeURIComponent(nameOrProduct || '')}`)
      .then(r => r.json())
      .then(data => {
        const list = data.results || data || [];
        const hit = list.find(p => (p.perfume_name || '').toLowerCase() === String(nameOrProduct || '').toLowerCase()) || list[0];
        if (hit) return goToProduct(hit);
        if (typeof legacyQuickView === 'function') return legacyQuickView(nameOrProduct, brand);
        window.location.href = '/shop/?search=' + encodeURIComponent(nameOrProduct || '');
      })
      .catch(() => { window.location.href = '/shop/'; });
  };

  window.TLN = {
    slugify, productUrl, goToProduct, toast,
    addToCart, refreshCartBadge, setCartBadge,
    toggleWishlist, getWishlist,
    recordView, getRecentlyViewed,
    api: { get, post },
  };

  document.addEventListener('DOMContentLoaded', refreshCartBadge);
})();
