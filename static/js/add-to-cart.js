// Add to Cart Function
function addToCart(productId, quantity = 1) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Please login first');
        window.location.href = '/accounts/login/';
        return;
    }
    
    const btn = document.getElementById('pdAddToCart') || event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Adding...';
    
    fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(r => r.json())
    .then(data => {
        showNotification(`✓ Added to cart! (${data.total_items} items)`);
        btn.textContent = '✓ ADDED TO CART';
        btn.disabled = true;
        
        // Update cart badge
        const badge = document.getElementById('cartBadge');
        if (badge) {
            badge.textContent = data.total_items;
            badge.style.display = 'block';
        }
        
        // Reload cart sidebar if it's open
        if (window.cartManager) {
            window.cartManager.loadCart();
        }
        
        // Reset button after 2 seconds
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        }, 2000);
    })
    .catch(err => {
        console.error('Error:', err);
        showNotification('Error adding to cart', 'error');
        btn.textContent = originalText;
        btn.disabled = false;
    });
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `position: fixed; top: 20px; right: 20px; background: ${type === 'success' ? '#27ae60' : '#e74c3c'}; color: white; padding: 15px 25px; border-radius: 4px; font-size: 14px; z-index: 10000;`;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function getCookie(name) {
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
    return cookieValue;
}

// Update cart badge on load
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    if (token) {
        fetch('/api/cart/', { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }})
        .then(r => r.json()).then(data => {
            const badge = document.getElementById('cartBadge');
            if (badge && data.total_items > 0) {
                badge.textContent = data.total_items;
                badge.style.display = 'block';
            }
        }).catch(err => console.log('Error:', err));
    }
});
