/* ═══════════════════════════════════════════════════════════════
   APP PREMIUM ENHANCEMENTS - Account & Navigation
   ═══════════════════════════════════════════════════════════════ */

/**
 * Handle account button click - route to customer panel if authenticated
 */
function handleAccountClick() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        // User is not logged in, show login modal
        showLoginModal();
    } else {
        // User is logged in, redirect to customer panel
        window.location.href = '/dashboard/';
    }
}

/**
 * Enhanced cart initialization with premium UI
 */
class EnhancedCart {
    constructor() {
        this.cart = this.loadCart();
        this.init();
    }

    loadCart() {
        try {
            return JSON.parse(localStorage.getItem('cart') || '[]');
        } catch {
            return [];
        }
    }

    init() {
        this.updateBadge();
        this.setupCartButton();
    }

    updateBadge() {
        const badge = document.getElementById('cartBadge');
        if (badge) {
            const count = this.cart.reduce((sum, item) => sum + item.quantity, 0);
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    }

    setupCartButton() {
        const cartBtn = document.getElementById('cartBtn');
        if (cartBtn) {
            cartBtn.addEventListener('click', () => this.viewCart());
        }
    }

    viewCart() {
        window.location.href = '/cart/';
    }
}

/**
 * Navigation enhancement - smooth scrolling and active states
 */
class NavEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupSmoothScroll();
        this.setupMobileNav();
        this.setupActiveStates();
    }

    setupSmoothScroll() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                const href = e.target.getAttribute('href');
                if (href === '#') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    }

    setupMobileNav() {
        const hamburger = document.getElementById('navHamburger');
        const overlay = document.getElementById('mobileNavOverlay');
        const panel = document.getElementById('mobileNavPanel');

        if (hamburger) {
            hamburger.addEventListener('click', () => {
                panel.setAttribute('aria-hidden', 'false');
                overlay.style.display = 'block';
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => this.closeMobileNav());
        }

        if (panel) {
            panel.querySelectorAll('a, button').forEach(link => {
                link.addEventListener('click', () => this.closeMobileNav());
            });
        }
    }

    closeMobileNav() {
        const overlay = document.getElementById('mobileNavOverlay');
        const panel = document.getElementById('mobileNavPanel');
        if (overlay) overlay.style.display = 'none';
        if (panel) panel.setAttribute('aria-hidden', 'true');
    }

    setupActiveStates() {
        const currentPage = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPage) {
                link.classList.add('active');
            }
        });
    }
}

/**
 * Authentication state management
 */
class AuthStateManager {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.init();
    }

    init() {
        this.updateAuthUI();
        this.checkTokenExpiry();
    }

    updateAuthUI() {
        const loginBtn = document.querySelector('button[onclick="showLoginModal()"]');
        const registerBtn = document.querySelector('button[onclick="showRegisterModal()"]');
        const accountBtn = document.getElementById('accountBtn');

        if (this.token) {
            // User is logged in
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';
            if (accountBtn) accountBtn.style.display = 'flex';
        } else {
            // User is logged out
            if (loginBtn) loginBtn.style.display = 'block';
            if (registerBtn) loginBtn.style.display = 'block';
            if (accountBtn) accountBtn.style.display = 'none';
        }
    }

    checkTokenExpiry() {
        // Implement token refresh logic here
        if (this.token) {
            // You can decode JWT and check expiry
            // For now, just check if it exists
            setTimeout(() => this.checkTokenExpiry(), 5 * 60 * 1000); // Check every 5 minutes
        }
    }

    isAuthenticated() {
        return !!this.token;
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_id');
        this.token = null;
        this.updateAuthUI();
        window.location.href = '/';
    }
}

/**
 * Product search enhancement
 */
class SearchEnhancer {
    constructor() {
        this.init();
    }

    init() {
        const searchTrigger = document.getElementById('searchTrigger');
        const searchInput = document.getElementById('searchInput');
        const searchDropdown = document.getElementById('searchDropdown');
        const searchCloseBtn = document.getElementById('searchCloseBtn');

        if (searchTrigger) {
            searchTrigger.addEventListener('click', () => {
                searchDropdown.setAttribute('aria-hidden', 'false');
                searchInput.focus();
            });
        }

        if (searchCloseBtn) {
            searchCloseBtn.addEventListener('click', () => {
                searchDropdown.setAttribute('aria-hidden', 'true');
                searchInput.value = '';
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
        }

        // Close search on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (searchDropdown) searchDropdown.setAttribute('aria-hidden', 'true');
            }
        });
    }

    performSearch(query) {
        if (!query || query.length < 2) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }

        fetch(`/api/search/?q=${encodeURIComponent(query)}`)
            .then(r => r.json())
            .then(results => this.renderSearchResults(results))
            .catch(err => console.error('Search error:', err));
    }

    renderSearchResults(results) {
        const container = document.getElementById('searchResults');
        
        if (!results || results.length === 0) {
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No results found</div>';
            return;
        }

        const html = results.slice(0, 5).map(result => `
            <a href="/product/${result.id}/" class="search-result-item">
                <div class="search-result-name">${result.name}</div>
                <div class="search-result-brand">${result.brand || 'Fragrance'}</div>
                <div class="search-result-price">৳${result.price}</div>
            </a>
        `).join('');

        container.innerHTML = html;
    }
}

/**
 * Toast notifications
 */
class ToastManager {
    static show(message, duration = 3000) {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    static success(message) {
        this.show(`✓ ${message}`);
    }

    static error(message) {
        this.show(`✗ ${message}`);
    }

    static info(message) {
        this.show(message);
    }
}

/**
 * Initialize all enhancements on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    window.cart = new EnhancedCart();
    window.nav = new NavEnhancer();
    window.auth = new AuthStateManager();
    window.search = new SearchEnhancer();
    window.toast = ToastManager;

    // Make toast globally available
    window.showToast = (msg) => ToastManager.show(msg);
});

/**
 * Expose logout function globally
 */
function logout() {
    if (window.auth) {
        window.auth.logout();
    }
}

/**
 * Add to cart helper
 */
function addToCartFromUI(productId, productName, price, image, brand) {
    if (!window.cart) return;
    
    const existing = window.cart.cart.find(item => item.id === productId);
    
    if (existing) {
        existing.quantity += 1;
    } else {
        window.cart.cart.push({
            id: productId,
            name: productName,
            price: price,
            image: image,
            brand: brand,
            quantity: 1
        });
    }
    
    localStorage.setItem('cart', JSON.stringify(window.cart.cart));
    window.cart.updateBadge();
    ToastManager.success(`${productName} added to cart`);
}
