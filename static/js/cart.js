/**
 * Cart Functionality Script
 * Integrates Premium Cart Sidebar + Existing Cart Features
 */

const getAuthToken = () => localStorage.getItem('access_token');

// ============================================
// CART SIDEBAR FUNCTIONALITY
// ============================================

const CartSidebar = {
    sidebar: null,
    overlay: null,
    
    init() {
        this.sidebar = document.getElementById('cartSidebar');
        this.overlay = document.getElementById('cartOverlay');
        
        if (!this.sidebar) return;
        
        // Event listeners
        document.getElementById('cartBtn')?.addEventListener('click', () => this.open());
        document.getElementById('cartSidebarClose')?.addEventListener('click', () => this.close());
        this.overlay?.addEventListener('click', () => this.close());
        document.getElementById('cartSidebarCheckout')?.addEventListener('click', () => this.checkout());
        document.getElementById('cartSidebarContinue')?.addEventListener('click', () => this.continueShopping());
        
        // Close on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.close();
        });
        
        // Load cart on page load
        this.loadCart();
    },
    
    open() {
        if (this.sidebar) {
            this.sidebar.classList.add('active');
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    close() {
        if (this.sidebar) {
            this.sidebar.classList.remove('active');
            this.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    },
    
    async loadCart() {
        try {
            const token = getAuthToken();
            if (!token) {
                this.renderEmpty();
                return;
            }
            
            const response = await fetch('/api/cart/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to load cart');
            
            const data = await response.json();
            
            if (!data.items || data.items.length === 0) {
                this.renderEmpty();
            } else {
                this.renderItems(data.items);
                this.renderSummary(data.total_price);
                updateCartBadge(data.total_items || 0);
            }
        } catch (error) {
            console.error('Error loading cart:', error);
            this.renderEmpty();
        }
    },
    
    renderEmpty() {
        const container = document.getElementById('cartSidebarItems');
        if (container) {
            container.innerHTML = `
                <div class="cart-sidebar-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                        <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                        <line x1="3" y1="6" x2="21" y2="6"/>
                        <path d="M16 10a4 4 0 0 1-8 0"/>
                    </svg>
                    <p>Your cart is empty</p>
                    <a href="/shop/" class="cart-sidebar-continue">Continue Shopping</a>
                </div>
            `;
        }
        document.getElementById('cartSidebarSummary')?.setAttribute('style', 'display: none;');
        document.getElementById('cartSidebarActions')?.setAttribute('style', 'display: none;');
    },
    
    renderItems(items) {
        const container = document.getElementById('cartSidebarItems');
        if (!container) return;
        
        const itemsHTML = items.map(item => `
            <div class="cart-sidebar-item" data-item-id="${item.id}">
                <img src="${item.product_image || '/static/images/placeholder.jpg'}" alt="${item.product_name}" class="cart-item-image">
                <div class="cart-item-details">
                    <h4 class="cart-item-name">${this.escapeHtml(item.product_name)}</h4>
                    <p class="cart-item-price">৳${parseFloat(item.price).toFixed(2)}</p>
                    <div class="cart-item-qty-control">
                        <button class="cart-item-qty-btn" onclick="CartSidebar.updateQuantity(${item.id}, ${item.quantity - 1})">−</button>
                        <span class="cart-item-qty">${item.quantity}</span>
                        <button class="cart-item-qty-btn" onclick="CartSidebar.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    </div>
                    <button class="cart-item-remove" onclick="CartSidebar.removeItem(${item.id})">Remove</button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = itemsHTML;
    },
    
    renderSummary(total) {
        document.getElementById('cartSidebarSubtotal').textContent = `৳${parseFloat(total).toFixed(2)}`;
        document.getElementById('cartSidebarTotal').textContent = `৳${parseFloat(total).toFixed(2)}`;
        document.getElementById('cartSidebarSummary')?.setAttribute('style', 'display: block;');
        document.getElementById('cartSidebarActions')?.setAttribute('style', 'display: block;');
    },
    
    async updateQuantity(itemId, newQuantity) {
        if (newQuantity < 1) {
            this.removeItem(itemId);
            return;
        }
        
        try {
            const token = getAuthToken();
            const response = await fetch(`/api/cart/items/${itemId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ quantity: newQuantity })
            });
            
            if (response.ok) {
                this.loadCart();
            }
        } catch (error) {
            console.error('Error updating quantity:', error);
        }
    },
    
    async removeItem(itemId) {
        try {
            const token = getAuthToken();
            const response = await fetch(`/api/cart/items/${itemId}/remove/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.loadCart();
            }
        } catch (error) {
            console.error('Error removing item:', error);
        }
    },
    
    checkout() {
        this.close();
        window.location.href = '/checkout/';
    },
    
    continueShopping() {
        this.close();
        window.location.href = '/shop/';
    },
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
};

// ============================================
// ADD TO CART FUNCTIONALITY
// ============================================

const addToCart = async (productId, quantity = 1) => {
    try {
        const authToken = getAuthToken();
        
        if (!authToken) {
            showNotification('Please login to add items to cart', 'error');
            window.location.href = '/';
            return;
        }
        
        const response = await fetch('/api/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add item to cart');
        }
        
        const result = await response.json();
        
        // Update cart badge
        updateCartBadge(result.total_items);
        
        // Show success message
        showNotification(`Added to cart! (${result.total_items} items)`, 'success');
        
        // Refresh sidebar if open
        if (CartSidebar.sidebar && CartSidebar.sidebar.classList.contains('active')) {
            CartSidebar.loadCart();
        }
        
        return result;
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error: ' + error.message, 'error');
    }
};

// ============================================
// CART BADGE & NOTIFICATIONS
// ============================================

const updateCartBadge = (count) => {
    const badge = document.querySelector('.cart-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
};

const loadCartCount = async () => {
    try {
        const authToken = getAuthToken();
        if (!authToken) {
            updateCartBadge(0);
            return;
        }
        
        const response = await fetch('/api/cart/', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateCartBadge(data.total_items || 0);
        }
    } catch (error) {
        console.error('Error loading cart:', error);
    }
};

const showNotification = (message, type = 'success') => {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
        color: white;
        padding: 15px 20px;
        border-radius: 4px;
        z-index: 10000;
        font-size: 14px;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
};

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load cart count
    loadCartCount();
    
    // Initialize cart sidebar
    CartSidebar.init();
    
    // Add slide in animation if not exists
    if (!document.querySelector('style[data-slideIn]')) {
        const style = document.createElement('style');
        style.setAttribute('data-slideIn', 'true');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
});
