/**
 * THE LAST NOTE - Premium Cart Page
 * Uses /api/cart/ and the project's real JWT key: access_token.
 */
(function () {
    'use strict';

    class PremiumCart {
        constructor() {
            this.apiBase = '/api/cart';
            this.token = localStorage.getItem('access_token') || localStorage.getItem('authToken');
            this.currentCart = null;
            this.init();
        }

        headers(json = false) {
            const h = { 'Accept': 'application/json' };
            if (json) h['Content-Type'] = 'application/json';
            if (this.token) h['Authorization'] = `Bearer ${this.token}`;
            return h;
        }

        async request(path = '', options = {}) {
            this.token = localStorage.getItem('access_token') || localStorage.getItem('authToken');
            const response = await fetch(`${this.apiBase}${path}`, {
                credentials: 'same-origin',
                ...options,
                headers: { ...this.headers(Boolean(options.body)), ...(options.headers || {}) }
            });
            const text = await response.text();
            let data = {};
            try { data = text ? JSON.parse(text) : {}; } catch (_) {}
            if (!response.ok) {
                const error = new Error(data.error || `Request failed (${response.status})`);
                error.status = response.status;
                throw error;
            }
            return data;
        }

        async init() {
            this.bindStaticButtons();
            if (!this.token) {
                this.showEmptyCart();
                this.toast('Please log in to view your cart.', 'warning');
                return;
            }
            await this.loadCart();
        }

        bindStaticButtons() {
            const checkout = document.getElementById('checkoutBtn');
            if (checkout) checkout.addEventListener('click', () => {
                if (!this.currentCart || !this.currentCart.items.length) return this.toast('Your cart is empty.', 'warning');
                window.location.href = '/checkout/';
            });
            const continueBtn = document.querySelector('.continue-shopping-btn');
            if (continueBtn) continueBtn.addEventListener('click', () => { window.location.href = '/shop/'; });
        }

        async loadCart() {
            this.showLoadingState();
            try {
                const data = await this.request('/');
                this.currentCart = data;
                this.updateBadge(data.total_items || 0);
                if (!data.items || !data.items.length) this.showEmptyCart();
                else {
                    this.renderCartItems(data.items);
                    this.updateSummary(data);
                }
            } catch (error) {
                console.error('Cart load error:', error);
                if (error.status === 401) {
                    this.token = null;
                    this.showEmptyCart();
                    this.toast('Your login session has expired. Please log in again.', 'warning');
                } else {
                    this.showError(error.message);
                }
            }
        }

        showLoadingState() {
            const l = document.getElementById('cartLoadingState');
            const e = document.getElementById('cartEmptyState');
            const c = document.getElementById('cartItemsContainer');
            if (l) l.style.display = 'flex';
            if (e) e.style.display = 'none';
            if (c) c.innerHTML = '';
        }

        showEmptyCart() {
            const l = document.getElementById('cartLoadingState');
            const e = document.getElementById('cartEmptyState');
            const c = document.getElementById('cartItemsContainer');
            if (l) l.style.display = 'none';
            if (e) e.style.display = 'block';
            if (c) c.innerHTML = '';
            this.updateSummary({ subtotal: 0, shipping: 0, tax: 0, total_price: 0, items: [] });
            this.updateBadge(0);
        }

        showError(message) {
            const l = document.getElementById('cartLoadingState');
            const e = document.getElementById('cartEmptyState');
            const c = document.getElementById('cartItemsContainer');
            if (l) l.style.display = 'none';
            if (e) {
                e.style.display = 'block';
                const title = e.querySelector('.empty-state-title');
                const desc = e.querySelector('.empty-state-description');
                if (title) title.textContent = 'Unable to load your cart';
                if (desc) desc.textContent = message || 'Please refresh and try again.';
            }
            if (c) c.innerHTML = '';
        }

        renderCartItems(items) {
            const c = document.getElementById('cartItemsContainer');
            const l = document.getElementById('cartLoadingState');
            const e = document.getElementById('cartEmptyState');
            if (!c) return;
            if (l) l.style.display = 'none';
            if (e) e.style.display = 'none';
            c.innerHTML = items.map(item => this.renderItem(item)).join('');
            c.querySelectorAll('[data-cart-action="increase"]').forEach(b => b.onclick = () => this.changeQuantity(b.dataset.itemId, Number(b.dataset.quantity) + 1));
            c.querySelectorAll('[data-cart-action="decrease"]').forEach(b => b.onclick = () => this.changeQuantity(b.dataset.itemId, Number(b.dataset.quantity) - 1));
            c.querySelectorAll('[data-cart-action="remove"]').forEach(b => b.onclick = () => this.removeItem(b.dataset.itemId));
        }

        renderItem(item) {
            const price = Number(item.final_price || item.price || 0);
            const subtotal = Number(item.subtotal || price * item.quantity);
            const image = item.image_url || item.image;
            const imageHtml = image ? `<img src="${this.escape(image)}" alt="${this.escape(item.product_name)}" loading="lazy">` : '<div class="cart-item-image-fallback">🧴</div>';
            return `
                <article class="cart-item-card" data-item-id="${item.id}" data-item-price="${price}">
                    <div class="cart-item-image">${imageHtml}</div>
                    <div class="cart-item-details">
                        <span class="cart-item-brand">${this.escape(item.brand || item.brand_name || 'THE LAST NOTE')}</span>
                        <h3 class="cart-item-name">${this.escape(item.product_name || item.perfume_name || 'Product')}</h3>
                        <div class="cart-item-variant">Unit price: ${this.money(price)}</div>
                        <div class="cart-item-price-row"><strong class="cart-item-subtotal">${this.money(subtotal)}</strong></div>
                    </div>
                    <div class="cart-item-controls">
                        <div class="quantity-selector">
                            <button class="qty-btn-control" data-cart-action="decrease" data-item-id="${item.id}" data-quantity="${item.quantity}" ${item.quantity <= 1 ? 'disabled' : ''}>−</button>
                            <span class="qty-input-display">${item.quantity}</span>
                            <button class="qty-btn-control" data-cart-action="increase" data-item-id="${item.id}" data-quantity="${item.quantity}" ${item.quantity >= item.stock_quantity ? 'disabled' : ''}>+</button>
                        </div>
                        <button class="cart-item-remove-btn" data-cart-action="remove" data-item-id="${item.id}">Remove</button>
                    </div>
                </article>`;
        }

        async changeQuantity(itemId, quantity) {
            const item = (this.currentCart.items || []).find(x => String(x.id) === String(itemId));
            if (!item || quantity < 1) return;
            if (quantity > Number(item.stock_quantity || 0)) return this.toast(`Only ${item.stock_quantity} available.`, 'warning');
            try {
                const data = await this.request(`/items/${itemId}/update/`, {
                    method: 'PATCH', body: JSON.stringify({ quantity })
                });
                this.currentCart = data;
                this.updateBadge(data.total_items || 0);
                if (data.items && data.items.length) { this.renderCartItems(data.items); this.updateSummary(data); }
                else this.showEmptyCart();
            } catch (e) { this.toast(e.message, 'error'); }
        }

        async removeItem(itemId) {
            try {
                const data = await this.request(`/items/${itemId}/remove/`, { method: 'DELETE' });
                this.currentCart = data;
                this.updateBadge(data.total_items || 0);
                if (data.items && data.items.length) { this.renderCartItems(data.items); this.updateSummary(data); }
                else this.showEmptyCart();
            } catch (e) { this.toast(e.message, 'error'); }
        }

        updateSummary(data) {
            const money = x => this.money(x);
            const sub = document.getElementById('summarySubtotal');
            const ship = document.getElementById('summaryShipping');
            const tax = document.getElementById('summaryTax');
            const total = document.getElementById('summaryTotal');
            if (sub) sub.textContent = money(data.subtotal || 0);
            if (ship) ship.textContent = Number(data.shipping || 0) === 0 ? 'Free' : money(data.shipping);
            if (tax) tax.textContent = money(data.tax || 0);
            if (total) total.textContent = money(data.total_price || 0);
            const btn = document.getElementById('checkoutBtn');
            if (btn) btn.disabled = !(data.items && data.items.length);
        }

        updateBadge(count) {
            document.querySelectorAll('#cartBadge, .cart-badge, [data-cart-count]').forEach(el => {
                el.textContent = count > 99 ? '99+' : String(count);
                el.style.display = count > 0 ? 'inline-flex' : 'none';
            });
        }

        money(value) { return '৳' + Number(value || 0).toLocaleString('en-BD', { minimumFractionDigits: 0, maximumFractionDigits: 2 }); }
        escape(value) { const d = document.createElement('div'); d.textContent = value == null ? '' : String(value); return d.innerHTML; }

        toast(message, type = 'info') {
            let el = document.getElementById('cartToast');
            if (!el) { el = document.createElement('div'); el.id = 'cartToast'; document.body.appendChild(el); }
            el.textContent = message;
            el.dataset.type = type;
            el.classList.add('show');
            clearTimeout(this.toastTimer);
            this.toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
        }
    }

    document.addEventListener('DOMContentLoaded', () => { window.premiumCart = new PremiumCart(); });
})();
