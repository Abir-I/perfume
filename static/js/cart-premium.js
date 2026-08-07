/* ═══════════════════════════════════════════════════════════════
   PREMIUM CART MODULE - Enhanced Add-to-Cart Experience
   ═══════════════════════════════════════════════════════════════ */

class PremiumCart {
  constructor() {
    this.cart = this.loadCart();
    this.setupEventListeners();
  }

  loadCart() {
    try {
      const stored = localStorage.getItem('cart');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  saveCart() {
    localStorage.setItem('cart', JSON.stringify(this.cart));
    this.updateCartBadge();
  }

  updateCartBadge() {
    const badge = document.getElementById('cartBadge');
    if (badge) {
      const total = this.cart.reduce((sum, item) => sum + item.quantity, 0);
      badge.textContent = total;
      badge.style.display = total > 0 ? 'flex' : 'none';
    }
  }

  setupEventListeners() {
    // Event delegation for add-to-cart buttons
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('add-to-cart-btn') || 
          e.target.closest('.add-to-cart-btn')) {
        e.preventDefault();
        const btn = e.target.closest('.add-to-cart-btn');
        this.showPremiumAddToCart(btn);
      }
    });
  }

  showPremiumAddToCart(button) {
    const productId = button.dataset.productId;
    const productName = button.dataset.productName;
    const productPrice = button.dataset.productPrice;
    const productImage = button.dataset.productImage;
    const productBrand = button.dataset.productBrand;

    const modal = this.createPremiumModal(productId, productName, productPrice, productImage, productBrand);
    document.body.appendChild(modal);

    // Trigger animation
    setTimeout(() => modal.classList.add('active'), 10);

    // Close handlers
    const closeBtn = modal.querySelector('.premium-cart-close');
    const overlay = modal.querySelector('.premium-cart-overlay');
    
    closeBtn.addEventListener('click', () => this.closePremiumModal(modal));
    overlay.addEventListener('click', () => this.closePremiumModal(modal));

    // Add to cart handler
    const confirmBtn = modal.querySelector('.premium-cart-confirm');
    confirmBtn.addEventListener('click', () => {
      this.addToCart(productId, productName, parseFloat(productPrice), productImage, productBrand);
      this.closePremiumModal(modal);
    });
  }

  createPremiumModal(productId, productName, productPrice, productImage, productBrand) {
    const modal = document.createElement('div');
    modal.className = 'premium-cart-modal';
    modal.innerHTML = `
      <div class="premium-cart-overlay"></div>
      <div class="premium-cart-panel">
        <button class="premium-cart-close" aria-label="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        
        <div class="premium-cart-content">
          <div class="premium-cart-image">
            <img src="${productImage || 'https://via.placeholder.com/200'}" alt="${productName}"/>
          </div>
          
          <div class="premium-cart-details">
            <p class="premium-cart-brand">${productBrand || 'Premium Fragrance'}</p>
            <h3 class="premium-cart-title">${productName}</h3>
            
            <div class="premium-cart-price-section">
              <span class="premium-cart-price">৳${parseFloat(productPrice).toLocaleString()}</span>
            </div>

            <div class="premium-cart-features">
              <div class="feature-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Authentic & Batch-Traced</span>
              </div>
              <div class="feature-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>Premium Packaging</span>
              </div>
              <div class="feature-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>Fast Delivery</span>
              </div>
            </div>

            <div class="premium-cart-actions">
              <button class="premium-cart-confirm" onclick="">
                <span>Add to Cart</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
              <button class="premium-cart-cancel" onclick="">
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    return modal;
  }

  closePremiumModal(modal) {
    modal.classList.remove('active');
    setTimeout(() => modal.remove(), 300);
  }

  addToCart(productId, productName, productPrice, productImage, productBrand) {
    const existing = this.cart.find(item => item.id === productId);
    
    if (existing) {
      existing.quantity += 1;
    } else {
      this.cart.push({
        id: productId,
        name: productName,
        price: productPrice,
        image: productImage,
        brand: productBrand,
        quantity: 1
      });
    }
    
    this.saveCart();
    this.showAddToCartToast();
  }

  showAddToCartToast() {
    const toast = document.getElementById('toast');
    if (toast) {
      toast.textContent = '✓ Added to cart';
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2500);
    }
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (!window.premiumCart) {
    window.premiumCart = new PremiumCart();
  }
});
