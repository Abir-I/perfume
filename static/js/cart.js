// Cart Functionality Script
// Connects product detail page to cart API

const getAuthToken = () => localStorage.getItem('authToken');

const addToCart = async (productId, quantity = 1) => {
    try {
        const authToken = getAuthToken();
        
        if (!authToken) {
            alert('Please login to add items to cart');
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
        
        // Update cart count in navbar
        updateCartBadge(result.total_items);
        
        // Show success message
        showNotification(`Added to cart! (${result.total_items} items)`);
        
        return result;
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error: ' + error.message, 'error');
    }
};

const updateCartBadge = (count) => {
    const badge = document.querySelector('.cart-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
};

const viewCart = () => {
    window.location.href = '/cart/';
};

// Add cart button click handler
document.addEventListener('DOMContentLoaded', () => {
    const cartBtn = document.getElementById('cartBtn');
    if (cartBtn) {
        cartBtn.addEventListener('click', viewCart);
    }
});

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

// Load cart count on page load
document.addEventListener('DOMContentLoaded', loadCartCount);

// Add CSS animation
const style = document.createElement('style');
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
