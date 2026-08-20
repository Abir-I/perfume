/* ══════════════════════════════════════════════════════════════
   SHOP PAGE — filters, product grid, pagination
   (API_BASE and showToast come from script.js, loaded before this)
   ══════════════════════════════════════════════════════════════ */

const PAGE_SIZE = 20;
const SHOP_FALLBACK_IMG = '/static/images/perfume-placeholder.svg';

function normalizeShopImageUrl(value) {
  if (!value) return SHOP_FALLBACK_IMG;
  let url = String(value).trim().replace(/\\/g, '/');
  if (/^(https?:|data:)/i.test(url)) return url;
  const mediaMatch = url.match(/(?:^|\/)media\/(.+)$/i);
  if (mediaMatch) return '/media/' + mediaMatch[1].replace(/^\/+/, '');
  url = url.replace(/^\/+/, '');
  if (url.startsWith('static/')) return '/' + url;
  if (url.startsWith('media/')) return '/' + url;
  if (url.startsWith('perfumes/')) return '/media/' + url;
  if (!url.includes('/')) return '/media/perfumes/' + url;
  return '/' + url;
}

const shopState = {
  brand_ids: [],
  min_price: null,
  max_price: null,
  product_type: '',
  volume: '',
  concentration: [],
  gender: [],
  season: [],
  page: 1,
};

const shopGrid       = document.getElementById('shopGrid');
const resultsCountEl = document.getElementById('resultsCount');
const paginationEl   = document.getElementById('shopPagination');
const chipsEl        = document.getElementById('activeFilterChips');

/* ══════════════════════════════════════════════════════════════
   BRAND LIST — fetched from the real API, rendered as checkboxes
   ══════════════════════════════════════════════════════════════ */
async function loadBrandFilters() {
  const listEl = document.getElementById('brandFilterList');
  try {
    const res = await fetch(`${API_BASE}/catalog/brands/`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    const brands = data.results || data;

    if (!brands.length) {
      listEl.innerHTML = '<p style="font-size:0.8rem;color:var(--c-fog);">No brands available.</p>';
      return;
    }

    listEl.innerHTML = brands.map(b => `
      <label class="filter-option">
        <input type="checkbox" name="brand_id" value="${b.brand_id}"/> ${b.brand_name}
      </label>
    `).join('');
  } catch {
    listEl.innerHTML = '<p style="font-size:0.8rem;color:var(--c-fog);">Couldn\'t load brands — check your connection.</p>';
  }
}

/* ══════════════════════════════════════════════════════════════
   BUILD QUERY PARAMS FROM CURRENT FILTER STATE
   ══════════════════════════════════════════════════════════════ */
function buildQueryParams() {
  const params = new URLSearchParams();
  shopState.brand_ids.forEach(id => params.append('brand_id', id));
  if (shopState.min_price) params.set('min_price', shopState.min_price);
  if (shopState.max_price) params.set('max_price', shopState.max_price);
  if (shopState.product_type) params.set('product_type', shopState.product_type);
  if (shopState.volume) params.set('volume', shopState.volume);
  shopState.concentration.forEach(c => params.append('concentration', c));
  shopState.gender.forEach(g => params.append('gender', g));
  shopState.season.forEach(s => params.append('season', s));
  params.set('limit', PAGE_SIZE);
  params.set('offset', (shopState.page - 1) * PAGE_SIZE);
  return params;
}

/* ══════════════════════════════════════════════════════════════
   FETCH + RENDER PRODUCTS
   ══════════════════════════════════════════════════════════════ */
async function loadShopProducts() {
  shopGrid.innerHTML = '<div class="shop-loading">Loading fragrances…</div>';
  resultsCountEl.textContent = 'Loading products…';

  try {
    const params = buildQueryParams();
    const res = await fetch(`${API_BASE}/catalog/products/?${params.toString()}`, { signal: AbortSignal.timeout(6000) });
    const data = await res.json();
    const products = data.results || [];
    const total = data.count || 0;

    renderShopGrid(products);
    renderResultsCount(total);
    renderPagination(total);
  } catch {
    shopGrid.innerHTML = '<div class="shop-empty">Couldn\'t reach the server. Check your connection and try again.</div>';
    resultsCountEl.textContent = '';
    paginationEl.innerHTML = '';
  }
}

function renderResultsCount(total) {
  if (total === 0) {
    resultsCountEl.textContent = 'No fragrances match these filters.';
  } else {
    const start = (shopState.page - 1) * PAGE_SIZE + 1;
    const end = Math.min(shopState.page * PAGE_SIZE, total);
    resultsCountEl.textContent = `Showing ${start}–${end} of ${total} fragrances`;
  }
}


function renderShopGrid(products) {
  if (!products.length) {
    shopGrid.innerHTML = '<div class="shop-empty">No fragrances match these filters — try clearing a few.</div>';
    return;
  }

  shopGrid.innerHTML = products.map(p => `
    <article class="shop-card" data-product-id="${p.product_id}" data-perfume-name="${(p.perfume_name || '').replace(/"/g, '')}" data-brand-name="${(p.brand_name || '').replace(/"/g, '')}" style="cursor:pointer">
      <div class="shop-card-img">
        <img
          src="${normalizeShopImageUrl(p.image_url)}"
          alt="${p.perfume_name}"
          loading="lazy"
          onerror="this.onerror=null;this.src='${SHOP_FALLBACK_IMG}'"
        />
      </div>
      <div class="shop-card-body">
        <p class="shop-card-brand">${p.brand_name || ''}</p>
        <p class="shop-card-name">${p.perfume_name}</p>
        <p class="shop-card-meta">${p.concentration || ''} · ${Number(p.volume_ml || 0)}ml · ${p.product_type === 'decant' ? 'Decant' : 'Full Size'}</p>
        <p class="shop-card-price">৳${Number(p.price || 0).toLocaleString()}</p>
      </div>
    </article>
  `).join('');
}

/* ══════════════════════════════════════════════════════════════
   PAGINATION
   ══════════════════════════════════════════════════════════════ */
function renderPagination(total) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  paginationEl.innerHTML = '';
  if (totalPages <= 1) return;

  const makeBtn = (label, page, opts = {}) => {
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (opts.active ? ' active' : '');
    btn.textContent = label;
    btn.disabled = !!opts.disabled;
    if (!opts.disabled && !opts.active) {
      btn.addEventListener('click', () => {
        shopState.page = page;
        loadShopProducts();
        window.scrollTo({ top: document.querySelector('.shop-main').offsetTop - 100, behavior: 'smooth' });
      });
    }
    return btn;
  };

  paginationEl.appendChild(makeBtn('‹ Prev', shopState.page - 1, { disabled: shopState.page === 1 }));

  const addEllipsis = () => {
    const span = document.createElement('span');
    span.className = 'page-ellipsis';
    span.textContent = '…';
    paginationEl.appendChild(span);
  };

  const pagesToShow = new Set([1, totalPages, shopState.page, shopState.page - 1, shopState.page + 1]);
  let lastShown = 0;
  [...pagesToShow].filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b).forEach(p => {
    if (p - lastShown > 1) addEllipsis();
    paginationEl.appendChild(makeBtn(String(p), p, { active: p === shopState.page }));
    lastShown = p;
  });

  paginationEl.appendChild(makeBtn('Next ›', shopState.page + 1, { disabled: shopState.page === totalPages }));
}

/* ══════════════════════════════════════════════════════════════
   ACTIVE FILTER CHIPS — shows what's applied, lets you remove one at a time
   ══════════════════════════════════════════════════════════════ */
function renderActiveChips() {
  const chips = [];

  document.querySelectorAll('#brandFilterList input:checked').forEach(cb => {
    chips.push({ label: cb.parentElement.textContent.trim(), clear: () => { cb.checked = false; } });
  });
  ['concentration', 'gender', 'season'].forEach(group => {
    document.querySelectorAll(`input[name="${group}"]:checked`).forEach(cb => {
      chips.push({ label: cb.value, clear: () => { cb.checked = false; } });
    });
  });
  if (shopState.min_price || shopState.max_price) {
    chips.push({
      label: `৳${shopState.min_price || 0} – ৳${shopState.max_price || '∞'}`,
      clear: () => {
        document.getElementById('minPriceInput').value = '';
        document.getElementById('maxPriceInput').value = '';
        shopState.min_price = null;
        shopState.max_price = null;
      },
    });
  }
  const typeChecked = document.querySelector('input[name="product_type"]:checked');
  if (typeChecked && typeChecked.value) {
    chips.push({
      label: typeChecked.value === 'decant' ? 'Decants Only' : 'Full-Size Only',
      clear: () => { document.querySelector('input[name="product_type"][value=""]').checked = true; },
    });
  }

  chipsEl.innerHTML = chips.map((c, i) => `
    <span class="filter-chip">${c.label} <button data-chip-index="${i}" aria-label="Remove filter">&times;</button></span>
  `).join('');

  chipsEl.querySelectorAll('button[data-chip-index]').forEach(btn => {
    btn.addEventListener('click', () => {
      chips[Number(btn.dataset.chipIndex)].clear();
      syncStateFromInputs();
      shopState.page = 1;
      loadShopProducts();
      renderActiveChips();
    });
  });
}

/* ══════════════════════════════════════════════════════════════
   SYNC STATE FROM CHECKBOXES/RADIOS, THEN REFETCH
   ══════════════════════════════════════════════════════════════ */
function syncStateFromInputs() {
  shopState.brand_ids = [...document.querySelectorAll('#brandFilterList input:checked')].map(cb => cb.value);
  shopState.concentration = [...document.querySelectorAll('input[name="concentration"]:checked')].map(cb => cb.value);
  shopState.gender = [...document.querySelectorAll('input[name="gender"]:checked')].map(cb => cb.value);
  shopState.season = [...document.querySelectorAll('input[name="season"]:checked')].map(cb => cb.value);
  const typeChecked = document.querySelector('input[name="product_type"]:checked');
  shopState.product_type = typeChecked ? typeChecked.value : '';
}

function refetchWithCurrentFilters() {
  syncStateFromInputs();
  shopState.page = 1;
  loadShopProducts();
  renderActiveChips();
}

/* Wire every filter checkbox/radio to refetch on change */
document.getElementById('shopSidebar').addEventListener('change', (e) => {
  if (e.target.matches('input[type="checkbox"], input[type="radio"]')) {
    refetchWithCurrentFilters();
  }
});

/* Price range has its own Apply button instead of firing on every keystroke */
document.getElementById('applyPriceBtn').addEventListener('click', () => {
  shopState.min_price = document.getElementById('minPriceInput').value || null;
  shopState.max_price = document.getElementById('maxPriceInput').value || null;
  shopState.page = 1;
  loadShopProducts();
  renderActiveChips();
});

/* Clear all filters */
document.getElementById('clearFiltersBtn').addEventListener('click', () => {
  document.querySelectorAll('#shopSidebar input[type="checkbox"]').forEach(cb => { cb.checked = false; });
  document.querySelector('input[name="product_type"][value=""]').checked = true;
  document.getElementById('minPriceInput').value = '';
  document.getElementById('maxPriceInput').value = '';
  Object.assign(shopState, {
    brand_ids: [], min_price: null, max_price: null, product_type: '',
    concentration: [], gender: [], season: [], page: 1,
  });
  loadShopProducts();
  renderActiveChips();
});

/* Mobile "Filters" toggle — sidebar is collapsed by default on ≤1024px */
document.getElementById('mobileFiltersToggle').addEventListener('click', () => {
  const sidebar = document.getElementById('shopSidebar');
  const chevron = document.getElementById('mobileFiltersChevron');
  const open = sidebar.classList.toggle('open');
  chevron.textContent = open ? '▴' : '▾';
});

/* ══════════════════════════════════════════════════════════════
   PRE-FILL FROM URL (?product_type=decant etc. from footer links)
   ══════════════════════════════════════════════════════════════ */
function applyFiltersFromURL() {
  const params = new URLSearchParams(window.location.search);
  const productType = params.get('product_type');
  shopState.volume = params.get('volume') || '';
  if (productType) {
    const radio = document.querySelector(`input[name="product_type"][value="${productType}"]`);
    if (radio) radio.checked = true;
  }
}

/* ══════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════ */
applyFiltersFromURL();
syncStateFromInputs();
loadBrandFilters();
loadShopProducts();
