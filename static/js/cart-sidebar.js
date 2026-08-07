/* THE LAST NOTE - Premium Cart Sidebar
 * IMPORTANT: this uses access_token, not authToken.
 * API: /api/cart/
 */
(function () {
    'use strict';

    class CartSidebar {
        constructor() {
            this.sidebar = document.getElementById('cartSidebar');
            this.overlay = document.getElementById('cartSidebarOverlay');
            this.closeButton = document.getElementById('cartSidebarClose');
            this.cartButton = document.getElementById('cartBtn');
            this.loading = document.getElementById('cartSidebarLoading');
            this.empty = document.getElementById('cartSidebarEmpty');
            this.content = document.getElementById('cartSidebarContent');
            this.items = document.getElementById('cartSidebarItems');
            this.footer = document.getElementById('cartSidebarFooter');
            this.subtotal = document.getElementById('cartSidebarSubtotal');
            this.shipping = document.getElementById('cartSidebarShipping');
            this.total = document.getElementById('cartSidebarTotal');
            this.checkout = document.getElementById('cartSidebarCheckout');
            this.continueButton = document.getElementById('cartSidebarContinue');
            this.viewCart = document.getElementById('cartSidebarViewCart');
            this.badge = document.getElementById('cartBadge');
            this.opened = false;
            this.cart = null;
            this.bind();
        }

        getToken() {
            return localStorage.getItem('access_token') || localStorage.getItem('authToken');
        }

        headers(json = false) {
            const h = { Accept: 'application/json' };
            if (json) h['Content-Type'] = 'application/json';
            const token = this.getToken();
            if (token) h.Authorization = `Bearer ${token}`;
            return h;
        }

        bind() {
            if (!this.sidebar || !this.cartButton) return;
            this.cartButton.addEventListener('click', e => { e.preventDefault(); this.open(); });
            if (this.closeButton) this.closeButton.onclick = () => this.close();
            if (this.overlay) this.overlay.onclick = () => this.close();
            document.addEventListener('keydown', e => { if (e.key === 'Escape' && this.opened) this.close(); });
            if (this.continueButton) this.continueButton.onclick = () => { this.close(); location.href = '/shop/'; };
            if (this.viewCart) this.viewCart.onclick = () => location.href = '/cart/';
            if (this.checkout) this.checkout.onclick = () => {
                if (this.cart && this.cart.items && this.cart.items.length) location.href = '/checkout/';
                else this.message('Your cart is empty.');
            };
            this.loadCount();
        }

        async open() {
            this.opened = true;
            this.sidebar.classList.add('is-open');
            if (this.overlay) this.overlay.classList.add('is-open');
            document.body.classList.add('cart-sidebar-open');
            this.sidebar.setAttribute('aria-hidden', 'false');
            await this.load();
        }

        close() {
            this.opened = false;
            this.sidebar.classList.remove('is-open');
            if (this.overlay) this.overlay.classList.remove('is-open');
            document.body.classList.remove('cart-sidebar-open');
            this.sidebar.setAttribute('aria-hidden', 'true');
        }

        async request(path = '', options = {}) {
            const response = await fetch('/api/cart/' + path.replace(/^\//, ''), {
                credentials: 'same-origin', ...options,
                headers: { ...this.headers(Boolean(options.body)), ...(options.headers || {}) }
            });
            const text = await response.text();
            let data = {};
            try { data = text ? JSON.parse(text) : {}; } catch (_) {}
            if (!response.ok) {
                const err = new Error(data.error || `Cart request failed (${response.status})`);
                err.status = response.status;
                throw err;
            }
            return data;
        }

        async loadCount() {
            if (!this.getToken()) return this.setBadge(0);
            try { const data = await this.request(''); this.setBadge(data.total_items || 0); } catch (_) {}
        }

        async load() {
            this.loadingState();
            if (!this.getToken()) return this.errorState('Please log in to view your cart.');
            try {
                const data = await this.request('');
                this.cart = data;
                this.setBadge(data.total_items || 0);
                if (!data.items || !data.items.length) this.emptyState();
                else { this.itemsState(); this.render(data.items); this.summary(data); }
            } catch (e) {
                console.error('Cart sidebar:', e);
                this.errorState(e.message);
            }
        }

        loadingState() {
            if (this.loading) this.loading.style.display = 'flex';
            if (this.empty) this.empty.style.display = 'none';
            if (this.content) this.content.style.display = 'none';
            if (this.footer) this.footer.style.display = 'none';
        }

        emptyState() {
            if (this.loading) this.loading.style.display = 'none';
            if (this.empty) this.empty.style.display = 'flex';
            if (this.content) this.content.style.display = 'none';
            if (this.footer) this.footer.style.display = 'none';
            this.setBadge(0);
        }

        itemsState() {
            if (this.loading) this.loading.style.display = 'none';
            if (this.empty) this.empty.style.display = 'none';
            if (this.content) this.content.style.display = 'block';
            if (this.footer) this.footer.style.display = 'block';
        }

        errorState(message) {
            if (this.loading) this.loading.style.display = 'none';
            if (this.content) this.content.style.display = 'none';
            if (this.footer) this.footer.style.display = 'none';
            if (this.empty) {
                this.empty.style.display = 'flex';
                const h = this.empty.querySelector('h3');
                const p = this.empty.querySelector('p');
                if (h) h.textContent = 'Unable to load your cart';
                if (p) p.textContent = message || 'Please refresh and try again.';
            }
        }

        render(items) {
            if (!this.items) return;
            this.items.innerHTML = items.map(item => {
                const price = Number(item.final_price || item.price || 0);
                const image = item.image_url || item.image;
                const img = image ? `<img src="${this.escape(image)}" alt="${this.escape(item.product_name)}" loading="lazy">` : '<div class="cart-sidebar-item-image-fallback">🧴</div>';
                return `<article class="cart-sidebar-item" data-cart-item-id="${item.id}">
                    <a class="cart-sidebar-item-image" href="/product/${item.product_id}/">${img}</a>
                    <div class="cart-sidebar-item-info">
                        <span class="cart-sidebar-item-brand">${this.escape(item.brand || item.brand_name || 'The Last Note')}</span>
                        <a class="cart-sidebar-item-name" href="/product/${item.product_id}/">${this.escape(item.product_name || item.perfume_name)}</a>
                        <div class="cart-sidebar-item-price">${this.money(price)}</div>
                        <div class="cart-sidebar-item-controls">
                            <div class="cart-sidebar-quantity">
                                <button type="button" class="cart-sidebar-qty-btn" data-action="decrease" data-id="${item.id}" ${item.quantity <= 1 ? 'disabled' : ''}>−</button>
                                <span class="cart-sidebar-qty-value">${item.quantity}</span>
                                <button type="button" class="cart-sidebar-qty-btn" data-action="increase" data-id="${item.id}" ${item.quantity >= item.stock_quantity ? 'disabled' : ''}>+</button>
                            </div>
                            <button type="button" class="cart-sidebar-remove" data-action="remove" data-id="${item.id}">Remove</button>
                        </div>
                    </div>
                </article>`;
            }).join('');

            this.items.querySelectorAll('[data-action="increase"]').forEach(b => b.onclick = () => this.change(b.dataset.id, 1));
            this.items.querySelectorAll('[data-action="decrease"]').forEach(b => b.onclick = () => this.change(b.dataset.id, -1));
            this.items.querySelectorAll('[data-action="remove"]').forEach(b => b.onclick = () => this.remove(b.dataset.id));
        }

        async change(id, delta) {
            const item = (this.cart.items || []).find(x => String(x.id) === String(id));
            if (!item) return;
            const quantity = item.quantity + delta;
            if (quantity < 1 || quantity > item.stock_quantity) return;
            try {
                const data = await this.request(`items/${id}/update/`, { method: 'PATCH', body: JSON.stringify({ quantity }) });
                this.cart = data; this.setBadge(data.total_items || 0);
                if (data.items && data.items.length) { this.render(data.items); this.summary(data); } else this.emptyState();
            } catch (e) { this.message(e.message); }
        }

        async remove(id) {
            try {
                const data = await this.request(`items/${id}/remove/`, { method: 'DELETE' });
                this.cart = data; this.setBadge(data.total_items || 0);
                if (data.items && data.items.length) { this.render(data.items); this.summary(data); } else this.emptyState();
            } catch (e) { this.message(e.message); }
        }

        summary(data) {
            if (this.subtotal) this.subtotal.textContent = this.money(data.subtotal);
            if (this.shipping) this.shipping.textContent = Number(data.shipping || 0) ? this.money(data.shipping) : 'Free';
            if (this.total) this.total.textContent = this.money(data.total_price);
            if (this.checkout) this.checkout.disabled = !(data.items && data.items.length);
        }

        setBadge(count) {
            if (!this.badge) return;
            this.badge.textContent = count > 99 ? '99+' : String(count);
            this.badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }

        money(v) { return '৳' + Number(v || 0).toLocaleString('en-BD', { maximumFractionDigits: 2 }); }
        escape(v) { const d = document.createElement('div'); d.textContent = v == null ? '' : String(v); return d.innerHTML; }
        message(text) { if (typeof window.showToast === 'function') window.showToast(text); else alert(text); }
    }

    function start() {
        if (window.__lastNoteCartSidebar) return;
        window.__lastNoteCartSidebar = new CartSidebar();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
    window.openCartSidebar = () => window.__lastNoteCartSidebar && window.__lastNoteCartSidebar.open();
    window.closeCartSidebar = () => window.__lastNoteCartSidebar && window.__lastNoteCartSidebar.close();
})();
