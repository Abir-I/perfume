/* ══════════════════════════════════════════════════════════════
   THE LAST NOTE · product-detail.js
   Gallery + zoom, quantity, AJAX cart, wishlist, tabs, reviews,
   related products and recently viewed for the dynamic
   Product Details page. Requires product-links.js (window.TLN).
   ══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const dataEl = document.getElementById('pd-data');
  if (!dataEl) return;

  const PRODUCT = JSON.parse(dataEl.textContent);
  const T = window.TLN;

  const money = n => '৳' + Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 2 });

  /* ══════════════ STAR RENDERING ══════════════ */
  function starSvg(filled) {
    return `<svg viewBox="0 0 24 24" class="${filled ? 's-on' : 's-off'}" stroke-width="1.4">
      <polygon points="12 2 15.1 8.6 22 9.5 17 14.5 18.2 21.5 12 18.2 5.8 21.5 7 14.5 2 9.5 8.9 8.6 12 2"/></svg>`;
  }

  function paintStars(root) {
    (root || document).querySelectorAll('.pd-stars').forEach(el => {
      const rating = Math.round(Number(el.dataset.rating || 0));
      el.innerHTML = [1, 2, 3, 4, 5].map(n => starSvg(n <= rating)).join('');
    });
  }
  paintStars();

  /* ══════════════ GALLERY + ZOOM ══════════════ */
  const stage = document.getElementById('pdStage');
  const mainImg = document.getElementById('pdMainImage');

  document.querySelectorAll('.pd-thumb').forEach(thumb => {
    thumb.addEventListener('click', () => {
      document.querySelectorAll('.pd-thumb').forEach(t => t.classList.remove('on'));
      thumb.classList.add('on');
      mainImg.style.opacity = '0';
      setTimeout(() => {
        mainImg.src = thumb.dataset.src;
        mainImg.style.opacity = '1';
      }, 150);
    });
  });

  if (stage && mainImg) {
    let locked = false;

    const moveZoom = e => {
      const rect = stage.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      mainImg.style.transformOrigin = `${Math.max(0, Math.min(100, x))}% ${Math.max(0, Math.min(100, y))}%`;
    };

    stage.addEventListener('mousemove', e => {
      if (!stage.classList.contains('zoomed')) return;
      moveZoom(e);
    });
    stage.addEventListener('mouseenter', e => {
      if (locked) return;
      stage.classList.add('zoomed');
      moveZoom(e);
    });
    stage.addEventListener('mouseleave', () => {
      if (locked) return;
      stage.classList.remove('zoomed');
      mainImg.style.transformOrigin = 'center center';
    });
    stage.addEventListener('click', e => {
      locked = !locked;
      stage.classList.toggle('zoomed', locked);
      if (locked) moveZoom(e);
      else mainImg.style.transformOrigin = 'center center';
    });
  }

  /* ══════════════ QUANTITY ══════════════ */
  const qtyInput = document.getElementById('pdQty');
  const maxQty = Math.max(1, Number(PRODUCT.stock_quantity || 1));

  function clampQty() {
    let v = parseInt(qtyInput.value, 10);
    if (isNaN(v) || v < 1) v = 1;
    if (v > maxQty) { v = maxQty; T.toast(`Only ${maxQty} in stock`); }
    qtyInput.value = v;
    return v;
  }

  document.getElementById('pdQtyMinus').addEventListener('click', () => {
    qtyInput.value = Math.max(1, (parseInt(qtyInput.value, 10) || 1) - 1);
    clampQty();
  });
  document.getElementById('pdQtyPlus').addEventListener('click', () => {
    qtyInput.value = (parseInt(qtyInput.value, 10) || 1) + 1;
    clampQty();
  });
  qtyInput.addEventListener('change', clampQty);

  /* ══════════════ ADD TO CART (AJAX) ══════════════ */
  const cartBtn = document.getElementById('pdAddToCart');
  if (cartBtn && !cartBtn.disabled) {
    cartBtn.addEventListener('click', async () => {
      const qty = clampQty();
      const original = cartBtn.textContent;
      cartBtn.disabled = true;
      cartBtn.textContent = 'Adding…';
      try {
        const data = await T.addToCart(PRODUCT.product_id, qty);
        cartBtn.classList.add('added');
        cartBtn.textContent = '✓ Added to Cart';
        T.toast(`${PRODUCT.perfume_name} · ${qty} added to cart (${data.total_items} items)`);
        setTimeout(() => {
          cartBtn.classList.remove('added');
          cartBtn.textContent = original;
          cartBtn.disabled = false;
        }, 2000);
      } catch (err) {
        cartBtn.textContent = original;
        cartBtn.disabled = false;
        T.toast(err.message || 'Could not add to cart');
      }
    });
  }

  /* ══════════════ WISHLIST ══════════════ */
  const wishBtn = document.getElementById('pdWishlist');
  const wishLabel = document.getElementById('pdWishlistLabel');
  if (wishBtn) {
    wishBtn.addEventListener('click', async () => {
      wishBtn.disabled = true;
      try {
        const data = await T.toggleWishlist(PRODUCT.product_id);
        wishBtn.classList.toggle('on', data.in_wishlist);
        wishBtn.setAttribute('aria-pressed', String(data.in_wishlist));
        wishBtn.querySelector('svg').setAttribute('fill', data.in_wishlist ? 'currentColor' : 'none');
        wishLabel.textContent = data.in_wishlist ? 'Saved' : 'Wishlist';
        T.toast(data.message);
      } catch (err) {
        T.toast(err.message || 'Could not update wishlist');
      } finally {
        wishBtn.disabled = false;
      }
    });
  }

  /* ══════════════ TABS ══════════════ */
  document.querySelectorAll('.pd-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.pd-tab').forEach(t => t.classList.remove('on'));
      document.querySelectorAll('.pd-panel').forEach(p => p.classList.remove('on'));
      tab.classList.add('on');
      document.getElementById('panel-' + tab.dataset.panel).classList.add('on');
    });
  });

  /* ══════════════ RATING BREAKDOWN ══════════════ */
  function renderBars(summary) {
    const bars = document.getElementById('pdBars');
    if (!bars) return;
    const total = summary.count || 0;
    bars.innerHTML = [5, 4, 3, 2, 1].map(star => {
      const n = (summary.breakdown && summary.breakdown[star]) || 0;
      const pct = total ? Math.round((n / total) * 100) : 0;
      return `<div class="pd-bar-row"><span>${star} star</span><div class="pd-bar"><i style="width:${pct}%"></i></div><span>${n}</span></div>`;
    }).join('');
  }
  renderBars(PRODUCT.rating);

  /* ══════════════ REVIEW SUBMISSION ══════════════ */
  let pickedRating = 0;
  const starPick = document.getElementById('pdStarPick');
  if (starPick) {
    starPick.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        pickedRating = Number(btn.dataset.value);
        starPick.querySelectorAll('button').forEach(b => {
          b.classList.toggle('on', Number(b.dataset.value) <= pickedRating);
        });
      });
    });
  }

  const reviewBtn = document.getElementById('pdReviewSubmit');
  if (reviewBtn) {
    reviewBtn.addEventListener('click', async () => {
      if (!pickedRating) { T.toast('Pick a star rating first'); return; }
      const comment = document.getElementById('pdReviewText').value.trim();
      reviewBtn.disabled = true;
      reviewBtn.textContent = 'Publishing…';
      try {
        const data = await T.api.post(`/catalog/products/${PRODUCT.product_id}/reviews/`, {
          rating: pickedRating,
          comment,
        });
        T.toast(data.message);
        document.getElementById('pdReviewText').value = '';
        starPick.querySelectorAll('button').forEach(b => b.classList.remove('on'));
        pickedRating = 0;
        await reloadReviews();
      } catch (err) {
        T.toast(err.status === 401 ? 'Please log in to write a review.' : (err.message || 'Could not publish review'));
        if (err.status === 401 && typeof window.showLoginModal === 'function') window.showLoginModal();
      } finally {
        reviewBtn.disabled = false;
        reviewBtn.textContent = 'Publish Review';
      }
    });
  }

  async function reloadReviews() {
    const data = await T.api.get(`/catalog/products/${PRODUCT.product_id}/reviews/`);
    const list = document.getElementById('pdReviewList');
    const results = data.results || [];
    list.innerHTML = results.length ? results.map(r => `
      <article class="pd-review">
        <div class="pd-review-top">
          <div>
            <span class="pd-reviewer">${r.user_name}</span>
            ${r.is_verified_purchase ? '<span class="pd-verified">Verified purchase</span>' : ''}
          </div>
          <div>
            <span class="pd-stars" data-rating="${r.rating}"></span>
            <span class="pd-review-date">${r.created_display}</span>
          </div>
        </div>
        <p>${(r.comment || 'No written comment.').replace(/</g, '&lt;')}</p>
      </article>`).join('')
      : '<p class="pd-empty">No reviews yet — be the first to share how this wears.</p>';

    const summary = data.summary || { average: 0, count: 0, breakdown: {} };
    document.getElementById('pdScore').textContent = summary.average;
    document.getElementById('pdScoreSub').textContent =
      `Based on ${summary.count} review${summary.count === 1 ? '' : 's'}`;
    document.getElementById('pdRatingText').textContent =
      `${summary.average} · ${summary.count} review${summary.count === 1 ? '' : 's'}`;
    document.querySelectorAll('.pd-stars[data-rating]').forEach(el => {
      if (el.id === 'pdStars' || el.closest('.pd-review-summary')) el.dataset.rating = summary.average;
    });
    renderBars(summary);
    paintStars();
  }

  /* ══════════════ RECENTLY VIEWED (kept fresh client-side) ══════════════ */
  function cardHtml(p) {
    return `
      <a class="pd-card" href="${p.url}">
        <div class="pd-card-img"><img src="${p.image_url || '/static/images/perfume-placeholder.svg'}" alt="${p.perfume_name}" loading="lazy" onerror="this.onerror=null;this.src='/static/images/perfume-placeholder.svg';"/></div>
        <div class="pd-card-body">
          <p class="pd-card-brand">${p.brand_name || ''}</p>
          <p class="pd-card-name">${p.perfume_name}</p>
          <p class="pd-card-meta">${p.concentration || ''} · ${Number(p.volume_ml || 0)}ml</p>
          <p class="pd-card-price">${money(p.price)}</p>
        </div>
      </a>`;
  }

  (async function syncRecent() {
    try {
      await T.recordView(PRODUCT.product_id);
      const data = await T.getRecentlyViewed(PRODUCT.product_id);
      const rail = document.getElementById('pdRecent');
      const section = document.getElementById('pdRecentSection');
      if (!rail || !section) return;
      if (data.results && data.results.length) {
        rail.innerHTML = data.results.map(cardHtml).join('');
        section.style.display = '';
      } else {
        section.style.display = 'none';
      }
    } catch (_) {}
  })();

  /* Keep the related rail fresh if the server render was empty */
  (async function ensureRelated() {
    const rail = document.getElementById('pdRelated');
    if (!rail || rail.querySelector('.pd-card')) return;
    try {
      const data = await T.api.get(`/catalog/products/${PRODUCT.product_id}/related/`);
      if (data.results && data.results.length) rail.innerHTML = data.results.map(cardHtml).join('');
    } catch (_) {}
  })();
})();
