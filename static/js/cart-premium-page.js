/**
 * Premium Cart Page
 * Complete cart management with AJAX interactions
 * The Last Note - Premium Perfume Shopping Experience
 */

class PremiumCart {
    constructor() {
        this.apiBase = '/api';
        this.currentCart = null;
        this.authToken = localStorage.getItem('access_token');
        this.isLoading = false;
        this.toastTimeout = null;
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize cart page
     */
    async init() {
        try {
            // Check authentication
            if (!this.authToken) {
                this.showEmptyCart();
                this.showToast('Please login to view your cart', 'warning');
                setTimeout(() => window.location.href = '/', 2000);
                return;
            }

            // Load cart data
            await this.loadCart();
        } catch (error) {
            console.error('Cart initialization error:', error);
            this.showToast('Failed to load cart', 'error');
        }
    }

    /**
     * Load cart from API
     */
    async loadCart() {
        try {
            this.isLoading = true;
            this.showLoadingState();

            const response = await fetch(`${this.apiBase}/cart/`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();

            // Handle cart data
            if (!data.items || data.items.length === 0) {
                this.showEmptyCart();
                this.updateSummary({ items: [], total_price: 0, subtotal: 0 });
            } else {
                this.currentCart = data;
                this.renderCartItems(data.items);
                this.updateSummary(data);
            }

            this.isLoading = false;
        } catch (error) {
            console.error('Error loading cart:', error);
            this.showToast('Failed to load cart items', 'error');
            this.isLoading = false;
        }
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const container = document.getElementById('cartItemsContainer');
        const emptyState = document.getElementById('cartEmptyState');
        const loadingState = document.getElementById('cartLoadingState');

        if (container) container.innerHTML = '';
        if (emptyState) emptyState.style.display = 'none';
        if (loadingState) loadingState.style.display = 'flex';
    }

    /**
     * Show empty cart state
     */
    showEmptyCart() {
        const loadingState = document.getElementById('cartLoadingState');
        const emptyState = document.getElementById('cartEmptyState');
        const container = document.getElementById('cartItemsContainer');

        if (loadingState) loadingState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
        if (container) container.innerHTML = '';
    }

    /**
     * Render cart items
     */
    renderCartItems(items) {
        const container = document.getElementById('cartItemsContainer');
        const loadingState = document.getElementById('cartLoadingState');
        const emptyState = document.getElementById('cartEmptyState');

        if (!container) return;

        // Clear loading state
        if (loadingState) loadingState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';

        // Render items
        container.innerHTML = items.map(item => this.renderCartItem(item)).join('');

        // Attach event listeners
        items.forEach(item => {
            this.attachItemEventListeners(item.id);
        });
    }

    /**
     * Render single cart item HTML
     */
    renderCartItem(item) {
        const imageUrl = item.image ? `/media/${item.image}` : null;
        const imageHtml = imageUrl 
            ? `<img src="${imageUrl}" alt="${item.product_name}" loading="lazy">`
            : `<div class="cart-item-image-fallback">🧴</div>`;

        const subtotal = (parseFloat(item.final_price || item.price) * item.quantity).toFixed(2);

        return `
            <div class="cart-item-card" data-item-id="${item.id}" data-item-price="${item.final_price || item.price}">
                <!-- Product Image -->
                <div class="cart-item-image">
                    ${imageHtml}
                </div>

                <!-- Item Details -->
                <div class="cart-item-details">
                    <span class="cart-item-brand">${this.escapeHtml(item.brand || 'BRAND')}</span>
                    <h3 class="cart-item-name">${this.escapeHtml(item.product_name)}</h3>
                    <div class="cart-item-variant">Quantity: <span data-qty-display="${item.id}">${item.quantity}</span> × <span class="cart-item-unit-price-amount">$${parseFloat(item.final_price || item.price).toFixed(2)}</span></div>
                    <div class="cart-item-price-row">
                        <span class="cart-item-subtotal" data-subtotal-display="${item.id}">$${subtotal}</span>
                    </div>
                </div>

                <!-- Controls -->
                <div class="cart-item-controls">
                    <div class="quantity-selector">
                        <button class="qty-btn-control qty-decrease" data-item-id="${item.id}" aria-label="Decrease quantity">−</button>
                        <input type="number" class="qty-input-display" value="${item.quantity}" min="1" max="100" data-qty-input="${item.id}" readonly>
                        <button class="qty-btn-control qty-increase" data-item-id="${item.id}" aria-label="Increase quantity">+</button>
                    </div>
                    <button class="cart-item-remove-btn" data-item-id="${item.id}" aria-label="Remove item from cart">
                        Remove
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners to cart item
     */
    attachItemEventListeners(itemId) {
        // Decrease quantity
        const decreaseBtn = document.querySelector(`[data-item-id="${itemId}"].qty-decrease`);
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => this.handleQuantityChange(itemId, 'decrease'));
        }

        // Increase quantity
        const increaseBtn = document.querySelector(`[data-item-id="${itemId}"].qty-increase`);
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => this.handleQuantityChange(itemId, 'increase'));
        }

        // Remove item
        const removeBtn = document.querySelector(`[data-item-id="${itemId}"].cart-item-remove-btn`);
        if (removeBtn) {
            removeBtn.addEventListener('click', () => this.handleRemoveItem(itemId));
        }
    }

    /**
     * Handle quantity change
     */
    async handleQuantityChange(itemId, direction) {
        try {
            const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
            if (!itemCard) return;

            const qtyInput = itemCard.querySelector(`[data-qty-input="${itemId}"]`);
            if (!qtyInput) return;

            let newQuantity = parseInt(qtyInput.value);

            if (direction === 'increase') {
                newQuantity++;
            } else if (direction === 'decrease') {
                if (newQuantity <= 1) {
                    this.showToast('Quantity must be at least 1', 'warning');
                    return;
                }
                newQuantity--;
            }

            // Disable controls during update
            this.disableItemControls(itemId, true);

            // Send update request
            const response = await fetch(`${this.apiBase}/cart/items/${itemId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({
                    quantity: newQuantity,
                    cart_id: this.currentCart.cart_id
                })
            });

            if (!response.ok) {
                throw new Error(`Update failed: ${response.status}`);
            }

            const result = await response.json();

            // Update UI
            this.updateItemQuantity(itemId, newQuantity);
            this.updateSummary(result);
            this.showToast('Quantity updated', 'success');

            // Enable controls
            this.disableItemControls(itemId, false);
        } catch (error) {
            console.error('Error updating quantity:', error);
            this.showToast('Failed to update quantity', 'error');
            this.disableItemControls(itemId, false);
        }
    }

    /**
     * Update item quantity in UI
     */
    updateItemQuantity(itemId, newQuantity) {
        const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemCard) return;

        // Update quantity display
        const qtyDisplay = itemCard.querySelector(`[data-qty-display="${itemId}"]`);
        const qtyInput = itemCard.querySelector(`[data-qty-input="${itemId}"]`);
        if (qtyDisplay) qtyDisplay.textContent = newQuantity;
        if (qtyInput) qtyInput.value = newQuantity;

        // Update subtotal
        const itemPrice = parseFloat(itemCard.dataset.itemPrice);
        const subtotal = (itemPrice * newQuantity).toFixed(2);
        const subtotalDisplay = itemCard.querySelector(`[data-subtotal-display="${itemId}"]`);
        if (subtotalDisplay) subtotalDisplay.textContent = `$${subtotal}`;

        // Animate update
        itemCard.style.opacity = '0.8';
        setTimeout(() => {
            itemCard.style.opacity = '1';
        }, 200);
    }

    /**
     * Handle item removal
     */
    async handleRemoveItem(itemId) {
        try {
            const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
            if (!itemCard) return;

            // Add removing class for animation
            itemCard.classList.add('removing');

            // Send delete request
            const response = await fetch(`${this.apiBase}/cart/items/${itemId}/remove/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Delete failed: ${response.status}`);
            }

            const result = await response.json();

            // Show success
            this.showToast('Item removed from cart', 'success');

            // Reload cart
            await this.loadCart();
        } catch (error) {
            console.error('Error removing item:', error);
            itemCard.classList.remove('removing');
            this.showToast('Failed to remove item', 'error');
        }
    }

    /**
     * Disable/enable item controls
     */
    disableItemControls(itemId, disabled) {
        const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemCard) return;

        const buttons = itemCard.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.disabled = disabled;
        });

        if (disabled) {
            itemCard.style.opacity = '0.6';
        } else {
            itemCard.style.opacity = '1';
        }
    }

    /**
     * Update summary section
     */
    updateSummary(data) {
        try {
            const subtotal = parseFloat(data.subtotal || 0).toFixed(2);
            const shipping = data.shipping || 'Free';
            const tax = parseFloat(data.tax || 0).toFixed(2);
            const total = parseFloat(data.total_price || 0).toFixed(2);

            // Update subtotal
            const subtotalEl = document.getElementById('summarySubtotal');
            if (subtotalEl) subtotalEl.textContent = `$${subtotal}`;

            // Update shipping
            const shippingEl = document.getElementById('summaryShipping');
            if (shippingEl) {
                shippingEl.textContent = shipping === 'Free' || shipping === '0' ? 'Free' : `$${parseFloat(shipping).toFixed(2)}`;
            }

            // Update tax
            const taxEl = document.getElementById('summaryTax');
            if (taxEl) taxEl.textContent = `$${tax}`;

            // Update total
            const totalEl = document.getElementById('summaryTotal');
            if (totalEl) {
                totalEl.textContent = `$${total}`;
                // Animate total update
                totalEl.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    totalEl.style.transform = 'scale(1)';
                }, 200);
            }

            // Update checkout button state
            const checkoutBtn = document.getElementById('checkoutBtn');
            if (checkoutBtn) {
                checkoutBtn.disabled = data.items && data.items.length === 0;
            }
        } catch (error) {
            console.error('Error updating summary:', error);
        }
    }

    /**
     * Proceed to checkout
     */
    proceedToCheckout() {
        try {
            if (!this.authToken) {
                this.showToast('Please login first', 'warning');
                return;
            }

            if (!this.currentCart || this.currentCart.items.length === 0) {
                this.showToast('Your cart is empty', 'warning');
                return;
            }

            // Navigate to checkout
            window.location.href = '/checkout/';
        } catch (error) {
            console.error('Checkout error:', error);
            this.showToast('Error proceeding to checkout', 'error');
        }
    }

    /**
     * Continue shopping
     */
    continueShopping() {
        window.location.href = '/shop/';
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        // Add icon
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <span>${this.escapeHtml(message)}</span>
        `;

        // Add to container
        container.appendChild(toast);

        // Auto-remove after delay
        const delay = type === 'error' ? 4000 : 3000;
        const timeout = setTimeout(() => {
            this.removeToast(toast);
        }, delay);

        // Add click to dismiss
        toast.addEventListener('click', () => {
            clearTimeout(timeout);
            this.removeToast(toast);
        });

        return toast;
    }

    /**
     * Remove toast notification
     */
    removeToast(toast) {
        if (!toast) return;
        toast.classList.add('removing');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    /**
     * Get toast icon SVG
     */
    getToastIcon(type) {
        const icons = {
            success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
            error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
            warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3.05h16.94a2 2 0 0 0 1.71-3.05L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
            info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
        };
        return icons[type] || icons.info;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global cart instance
let premiumCart = null;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        premiumCart = new PremiumCart();
    });
} else {
    premiumCart = new PremiumCart();
}

// Global functions for inline event handlers
function proceedToCheckout() {
    if (premiumCart) premiumCart.proceedToCheckout();
}

function continueShopping() {
    if (premiumCart) premiumCart.continueShopping();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PremiumCart;
}
