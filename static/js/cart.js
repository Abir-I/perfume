/* Shared cart helper. The real login token is access_token. */
(function () {
    'use strict';

    const TOKEN_KEYS = ['access_token', 'authToken'];
    const token = () => {
        for (const key of TOKEN_KEYS) {
            const value = localStorage.getItem(key);
            if (value) return value;
        }
        return null;
    };

    window.TheLastNoteCart = {
        token,
        headers(json = false) {
            const h = { 'Accept': 'application/json' };
            if (json) h['Content-Type'] = 'application/json';
            const t = token();
            if (t) h['Authorization'] = `Bearer ${t}`;
            return h;
        },
        async get() {
            const r = await fetch('/api/cart/', { headers: this.headers(), credentials: 'same-origin' });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || `Cart request failed (${r.status})`);
            return d;
        },
        async add(productId, quantity = 1) {
            const r = await fetch('/api/cart/add/', {
                method: 'POST', credentials: 'same-origin',
                headers: this.headers(true), body: JSON.stringify({ product_id: productId, quantity })
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || 'Unable to add to cart');
            this.updateBadge(d.total_items || 0);
            return d;
        },
        updateBadge(count) {
            document.querySelectorAll('#cartBadge, .cart-badge, [data-cart-count]').forEach(el => {
                el.textContent = count > 99 ? '99+' : String(count);
                el.style.display = count > 0 ? 'inline-flex' : 'none';
            });
        }
    };
})();
