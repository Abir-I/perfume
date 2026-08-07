/**
 * PERFUME E-COMMERCE - MAIN APPLICATION
 * Complete Frontend Application Controller
 * =============================================
 */

class PerfumeEcommerce {
    constructor() {
        this.apiBase = '/api';
        this.currentUser = null;
        this.cart = null;
        this.token = localStorage.getItem('access_token');
        
        this.init();
    }

    async init() {
        console.log('🚀 Perfume App Initializing...');
        
        // Check if user is authenticated
        if (this.token) {
            await this.loadUserData();
        }

        // Setup all event listeners
        this.setupEventListeners();

        // Load cart count
        if (this.token) {
            await this.loadCartCount();
        }

        console.log('✅ App Ready');
    }

    // ========================================================================
    // AUTHENTICATION
    // ========================================================================

    async loadUserData() {
        try {
            const response = await fetch(`${this.apiBase}/accounts/dashboard/`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateUIForLoggedUser();
            } else {
                // Token might be expired
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                    this.token = null;
                }
            }
        } catch (error) {
            console.log('Not authenticated');
        }
    }

    updateUIForLoggedUser() {
        // Hide login button
        const loginBtn = document.querySelector('[data-action="open-login"]');
        if (loginBtn) loginBtn.style.display = 'none';

        // Show user menu
        const userMenu = document.querySelector('[data-user-menu]');
        if (userMenu) {
            userMenu.style.display = 'flex';
            const userName = userMenu.querySelector('[data-user-name]');
            if (userName) userName.textContent = this.currentUser.name.split(' ')[0];
        }

        // Update all account links
        const accountLinks = document.querySelectorAll('[data-action="open-dashboard"]');
        accountLinks.forEach(link => {
            link.href = '/dashboard/';
            link.onclick = () => {
                window.location.href = '/dashboard/';
            };
        });
    }

    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-action]');
            if (!target) return;

            const action = target.dataset.action;

            switch(action) {
                case 'add-to-cart':
                    e.preventDefault();
                    this.handleAddToCart(target);
                    break;
                    
                case 'open-dashboard':
                    e.preventDefault();
                    this.openDashboard();
                    break;

                case 'open-cart':
                    e.preventDefault();
                    window.location.href = '/cart/';
                    break;

                case 'logout':
                    e.preventDefault();
                    this.logout();
                    break;

                case 'open-login':
                    e.preventDefault();
                    this.openLoginModal();
                    break;
            }
        });
    }

    // ========================================================================
    // ADD TO CART - MAIN FEATURE
    // ========================================================================

    async handleAddToCart(button) {
        if (!this.token) {
            this.showNotification('Please login to add items to cart', 'warning');
            this.openLoginModal();
            return;
        }

        const productId = button.dataset.productId;
        const quantity = parseInt(button.dataset.quantity || 1);

        if (!productId) {
            this.showNotification('Product not found', 'error');
            return;
        }

        try {
            // Show loading state
            const originalText = button.textContent;
            const originalClass = button.className;
            button.disabled = true;
            button.textContent = '⏳ Adding...';
            button.style.opacity = '0.7';

            // Add to cart API call
            const response = await fetch(`${this.apiBase}/cart/add/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            });

            const data = await response.json();

            if (response.ok) {
                // SUCCESS - Show animation and feedback
                button.textContent = '✅ Added!';
                button.style.background = '#4CAF50';

                // Update cart count
                this.updateCartBadge(data.total_items);

                // Show notification
                this.showNotification(`✅ Added to cart! (${data.total_items} items)`, 'success');

                // Animate button
                this.animateButton(button);

                // Reset after delay
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = originalText;
                    button.className = originalClass;
                    button.style.opacity = '1';
                    button.style.background = '';
                }, 2000);

            } else {
                // ERROR
                this.showNotification(`❌ ${data.error || 'Failed to add to cart'}`, 'error');
                button.disabled = false;
                button.textContent = originalText;
                button.style.opacity = '1';
            }

        } catch (error) {
            console.error('Add to cart error:', error);
            this.showNotification('❌ Error adding to cart', 'error');
            button.disabled = false;
            button.textContent = originalText;
            button.style.opacity = '1';
        }
    }

    animateButton(button) {
        // Add scale animation
        button.style.transform = 'scale(1.05)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 100);
    }

    async loadCartCount() {
        try {
            const response = await fetch(`${this.apiBase}/cart/`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateCartBadge(data.total_items);
            }
        } catch (error) {
            console.log('Error loading cart');
        }
    }

    updateCartBadge(count) {
        const badge = document.querySelector('[data-cart-count]');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    }

    // ========================================================================
    // NAVIGATION
    // ========================================================================

    openDashboard() {
        if (!this.currentUser) {
            this.showNotification('Please login first', 'warning');
            this.openLoginModal();
            return;
        }

        window.location.href = '/dashboard/';
    }

    openLoginModal() {
        // Trigger login modal if it exists
        const modal = document.querySelector('[data-modal="login"]');
        if (modal) {
            modal.style.display = 'block';
        } else {
            // Redirect to login page or show inline login
            window.location.href = '/?login=true';
        }
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            this.currentUser = null;
            this.token = null;
            this.showNotification('Logged out successfully', 'success');
            
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    }

    // ========================================================================
    // UTILITIES
    // ========================================================================

    showNotification(message, type = 'info') {
        // Check if notification container exists
        let container = document.querySelector('[data-notifications]');
        if (!container) {
            container = document.createElement('div');
            container.setAttribute('data-notifications', '');
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.style.cssText = `
            padding: 15px 20px;
            border-radius: 4px;
            margin-bottom: 10px;
            animation: slideInRight 0.3s ease;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        `;

        const colors = {
            success: { bg: '#4CAF50', text: 'white' },
            error: { bg: '#f44336', text: 'white' },
            warning: { bg: '#ff9800', text: 'white' },
            info: { bg: '#2196F3', text: 'white' }
        };

        const color = colors[type] || colors.info;
        notification.style.backgroundColor = color.bg;
        notification.style.color = color.text;
        notification.textContent = message;

        container.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;

        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        return cookieValue || '';
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PerfumeEcommerce();
    
    // Add CSS animations
    addAnimationStyles();
});

function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }

        [data-action="add-to-cart"] {
            transition: all 0.3s ease !important;
        }

        [data-action="add-to-cart"]:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
        }

        [data-action="add-to-cart"]:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// GLOBAL FUNCTIONS (for inline onclick handlers)
// ============================================================================

window.addToCart = function(productId, quantity = 1) {
    if (window.app) {
        const button = event.target;
        button.dataset.productId = productId;
        button.dataset.quantity = quantity;
        window.app.handleAddToCart(button);
    }
};

window.goToDashboard = function() {
    if (window.app) {
        window.app.openDashboard();
    }
};

window.logout = function() {
    if (window.app) {
        window.app.logout();
    }
};

window.openLogin = function() {
    if (window.app) {
        window.app.openLoginModal();
    }
};
