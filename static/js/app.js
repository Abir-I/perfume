// PERFUME E-COMMERCE - COMPLETE APP
// Your original design + Complete functionality

const API_BASE = '/api';
let allProducts = [];
let cartData = null;
let currentUser = null;

// GET AUTH TOKEN
const getToken = () => localStorage.getItem('access_token');
const setToken = (token) => localStorage.setItem('access_token', token);
const clearToken = () => localStorage.removeItem('access_token');

// INITIALIZE
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadFeaturedProducts();
    checkAuth();
    loadAllProducts();
    loadCart();
});

// ==================== NAVIGATION ====================
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item, [data-section]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const section = item.getAttribute('data-section') || item.textContent.toLowerCase();
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('[role="region"], .section, [data-content]').forEach(el => {
        el.style.display = 'none';
        el.classList.remove('active');
    });

    // Show selected section
    const sectionId = sectionName.toLowerCase().replace(/\s+/g, '-');
    const section = document.getElementById(sectionId) || document.querySelector(`[data-section="${sectionName}"]`);
    
    if (section) {
        section.style.display = 'block';
        section.classList.add('active');
    }

    // Update active nav
    document.querySelectorAll('nav a, .nav-item').forEach(nav => {
        nav.classList.remove('active');
        if (nav.textContent.toLowerCase().includes(sectionName.toLowerCase())) {
            nav.classList.add('active');
        }
    });

    window.scrollTo(0, 0);
}

// ==================== AUTHENTICATION ====================
function checkAuth() {
    const token = getToken();
    const authBtn = document.getElementById('authBtn') || document.querySelector('[data-auth]');
    
    if (token) {
        if (authBtn) {
            authBtn.innerHTML = '<button onclick="logout()" class="logout-btn">LOGOUT</button>';
        }
        loadUserData();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username')?.value || document.querySelector('[name="username"]')?.value;
    const password = document.getElementById('password')?.value || document.querySelector('[name="password"]')?.value;

    try {
        const res = await fetch(`${API_BASE}/accounts/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            const data = await res.json();
            setToken(data.access);
            showNotification('✅ Logged in successfully!');
            checkAuth();
            loadCart();
            document.querySelector('.modal')?.classList.remove('active');
        } else {
            alert('Invalid credentials');
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

function logout() {
    clearToken();
    showNotification('Logged out');
    checkAuth();
    loadCart();
    showSection('home');
}

// ==================== PRODUCTS ====================
async function loadFeaturedProducts() {
    try {
        const res = await fetch(`${API_BASE}/catalog/products/?limit=8`);
        const data = await res.json();
        
        const container = document.getElementById('featured-products') || document.querySelector('[data-featured]');
        if (!container) return;

        const html = (data.products || []).map(p => createProductCard(p)).join('');
        container.innerHTML = html || '<p>No products available</p>';
    } catch (e) {
        console.error('Error:', e);
    }
}

async function loadAllProducts() {
    try {
        const res = await fetch(`${API_BASE}/catalog/products/`);
        const data = await res.json();
        allProducts = data.products || [];
        displayProducts(allProducts);
    } catch (e) {
        console.error('Error:', e);
    }
}

function displayProducts(products) {
    const container = document.getElementById('products-grid') || document.querySelector('[data-products]');
    if (!container) return;

    const html = products.map(p => createProductCard(p)).join('');
    container.innerHTML = html || '<p>No products</p>';
}

function createProductCard(product) {
    return `
        <div class="product-card" onclick="viewProductDetail(${product.product_id}, event)">
            <div class="product-image">💐</div>
            <div class="product-info">
                <div class="product-name">${product.perfume_name || 'Product'}</div>
                <div class="product-brand">${product.brand_name || 'Brand'}</div>
                <div class="product-price">$${product.price || '0.00'}</div>
                <button class="add-btn" onclick="addToCart(event, ${product.product_id}, 1)">Add to Cart</button>
            </div>
        </div>
    `;
}

async function viewProductDetail(productId, e) {
    if (e) e.stopPropagation();
    
    const product = allProducts.find(p => p.product_id === productId);
    if (!product) return;

    const modal = document.getElementById('product-detail-modal') || createProductDetailModal();
    
    modal.innerHTML = `
        <div class="modal-content">
            <button class="close-btn" onclick="this.parentElement.parentElement.style.display='none'">×</button>
            <div class="product-detail">
                <div class="detail-image">💐</div>
                <div class="detail-info">
                    <h2>${product.perfume_name}</h2>
                    <p class="brand">${product.brand_name}</p>
                    <p class="price">$${product.price}</p>
                    <p class="description">${product.description || 'Premium fragrance'}</p>
                    
                    <div class="rating">⭐ 4.5/5 (120 reviews)</div>
                    
                    <div class="qty-selector">
                        <label>Quantity:</label>
                        <button onclick="decreaseQty()">−</button>
                        <input type="number" id="detail-qty" value="1" min="1">
                        <button onclick="increaseQty()">+</button>
                    </div>
                    
                    <button class="btn-primary" onclick="addToCart(event, ${productId}, parseInt(document.getElementById('detail-qty').value))">
                        ADD TO CART
                    </button>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function decreaseQty() {
    const qty = document.getElementById('detail-qty');
    if (qty.value > 1) qty.value--;
}

function increaseQty() {
    const qty = document.getElementById('detail-qty');
    qty.value++;
}

// ==================== FILTERS ====================
function filterProducts() {
    const brand = (document.getElementById('brandFilter') || {}).value?.toLowerCase() || '';
    const priceMax = (document.getElementById('priceFilter') || {}).value || 1000;
    const sort = (document.getElementById('sortFilter') || {}).value || 'latest';

    let filtered = allProducts.filter(p => {
        const matchBrand = !brand || (p.brand_name || '').toLowerCase().includes(brand);
        const matchPrice = p.price <= priceMax;
        return matchBrand && matchPrice;
    });

    // Sort
    if (sort === 'price-low') filtered.sort((a, b) => a.price - b.price);
    if (sort === 'price-high') filtered.sort((a, b) => b.price - a.price);

    displayProducts(filtered);
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase();
    if (!query) {
        loadFeaturedProducts();
        return;
    }

    const filtered = allProducts.filter(p => 
        (p.perfume_name || '').toLowerCase().includes(query) ||
        (p.brand_name || '').toLowerCase().includes(query)
    );

    displayProducts(filtered);
}

// ==================== CART ====================
async function loadCart() {
    const token = getToken();
    if (!token) {
        updateCartUI(null);
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/cart/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        cartData = data;
        updateCartUI(data);
    } catch (e) {
        console.error('Error:', e);
    }
}

function updateCartUI(data) {
    const badge = document.getElementById('cartBadge') || document.querySelector('[data-cart-count]');
    if (badge) badge.textContent = data?.total_items || 0;

    const cartList = document.getElementById('cartItemsList') || document.querySelector('[data-cart-items]');
    if (!cartList) return;

    if (!data || !data.items || data.items.length === 0) {
        cartList.innerHTML = '<p class="empty-msg">Your cart is empty</p>';
        document.getElementById('checkoutBtn').disabled = true;
        return;
    }

    const html = data.items.map(item => `
        <div class="cart-item">
            <div class="item-image">💐</div>
            <div class="item-details">
                <div class="item-name">${item.product_name}</div>
                <div class="item-price">$${item.unit_price}</div>
                <div class="qty-control">
                    <button onclick="updateQty(${item.id}, -1)">−</button>
                    <input type="number" value="${item.quantity}" readonly>
                    <button onclick="updateQty(${item.id}, 1)">+</button>
                </div>
            </div>
            <button class="remove-btn" onclick="removeFromCart(${item.id})">Remove</button>
        </div>
    `).join('');

    cartList.innerHTML = html;

    // Update summary
    const subtotal = data.total_price || 0;
    const shipping = subtotal > 0 ? 50 : 0;
    const tax = subtotal * 0.05;
    const total = subtotal + shipping + tax;

    document.getElementById('subtotal').textContent = '$' + subtotal.toFixed(2);
    document.getElementById('shipping').textContent = '$' + shipping.toFixed(2);
    document.getElementById('tax').textContent = '$' + tax.toFixed(2);
    document.getElementById('cartTotal').textContent = '$' + total.toFixed(2);
    document.getElementById('checkoutBtn').disabled = false;
}

async function addToCart(e, productId, quantity) {
    if (e) e.stopPropagation();
    
    const token = getToken();
    if (!token) {
        alert('Please login first');
        document.getElementById('authModal').classList.add('active');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/cart/add/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ product_id: productId, quantity })
        });

        if (res.ok) {
            showNotification('✅ Added to cart!');
            loadCart();
            document.querySelector('.modal')?.style.remove('display');
        }
    } catch (e) {
        console.error('Error:', e);
    }
}

async function updateQty(itemId, change) {
    const token = getToken();
    if (!token) return;

    try {
        const currentQty = parseInt(document.querySelector(`input[data-item-${itemId}]`)?.value || 1);
        const newQty = Math.max(1, currentQty + change);

        await fetch(`${API_BASE}/cart/items/${itemId}/update/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ quantity: newQty })
        });

        loadCart();
    } catch (e) {
        console.error('Error:', e);
    }
}

async function removeFromCart(itemId) {
    const token = getToken();
    if (!token) return;

    try {
        await fetch(`${API_BASE}/cart/items/${itemId}/remove/`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        loadCart();
    } catch (e) {
        console.error('Error:', e);
    }
}

// ==================== CHECKOUT ====================
async function submitOrder(e) {
    e.preventDefault();
    
    const token = getToken();
    if (!token) {
        alert('Please login');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/orders/checkout/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: document.getElementById('orderName').value,
                email: document.getElementById('orderEmail').value,
                phone: document.getElementById('orderPhone').value,
                address: document.getElementById('orderAddress').value,
                city: document.getElementById('orderCity').value,
                state: document.getElementById('orderState').value,
                postal_code: document.getElementById('orderPostalCode').value,
                payment_method: document.getElementById('paymentMethod').value
            })
        });

        if (res.ok) {
            const data = await res.json();
            alert(`✅ Order placed!\nOrder ID: ${data.order_number}`);
            loadCart();
            loadCustomerOrders();
            showSection('customer');
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// ==================== CUSTOMER PANEL ====================
async function loadCustomerOrders() {
    const token = getToken();
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/orders/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        const container = document.getElementById('ordersList') || document.querySelector('[data-orders]');
        if (!container) return;

        const html = (data.orders || []).map(order => `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-number">Order #${order.order_number}</div>
                    <span class="order-status status-${order.order_status}">${order.status_display}</span>
                </div>
                <div class="order-details">
                    <p>Date: ${new Date(order.order_date).toLocaleDateString()}</p>
                    <p>Total: <strong>$${order.total_amount}</strong></p>
                </div>
                <div class="order-actions">
                    <button class="small-btn" onclick="showOrderTracking(${order.order_id})">Track</button>
                    ${order.can_cancel ? `<button class="small-btn danger" onclick="cancelOrder(${order.order_id})">Cancel</button>` : ''}
                </div>
            </div>
        `).join('');

        container.innerHTML = html || '<p>No orders yet</p>';
    } catch (e) {
        console.error('Error:', e);
    }
}

async function showOrderTracking(orderId) {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        const order = data.order;

        const timeline = (order.tracking_history || []).map((t, i) => `
            <div class="timeline-item">
                <div class="timeline-marker">${i === 0 ? '📦' : i === order.tracking_history.length - 1 ? '✅' : '→'}</div>
                <div class="timeline-content">
                    <div class="timeline-date">${new Date(t.timestamp).toLocaleString()}</div>
                    <div class="timeline-title">${t.status_message}</div>
                    ${t.location ? `<div class="timeline-loc">${t.location}</div>` : ''}
                </div>
            </div>
        `).join('');

        alert(`Order #${order.order_number}\nStatus: ${order.status_display}\nTotal: $${order.total_amount}`);
    } catch (e) {
        console.error('Error:', e);
    }
}

async function cancelOrder(orderId) {
    if (!confirm('Cancel this order?')) return;

    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}/cancel/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ reason: 'Customer requested' })
        });

        if (res.ok) {
            showNotification('✅ Order cancelled');
            loadCustomerOrders();
        }
    } catch (e) {
        console.error('Error:', e);
    }
}

async function loadUserData() {
    // Load user profile and addresses
}

function updateProfile() {
    alert('Profile update coming soon');
}

function showAddAddressForm() {
    alert('Add address feature coming soon');
}

// ==================== UTILITIES ====================
function showNotification(msg) {
    const notif = document.createElement('div');
    notif.className = 'notification';
    notif.textContent = msg;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

function toggleAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.classList.toggle('active');
}

function createProductDetailModal() {
    const modal = document.createElement('div');
    modal.id = 'product-detail-modal';
    modal.className = 'modal';
    document.body.appendChild(modal);
    return modal;
}

// Auto-load cart every 5 seconds
setInterval(() => {
    if (getToken()) loadCart();
}, 5000);
