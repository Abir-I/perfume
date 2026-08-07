/* ═══════════════════════════════════════════════════════════════════════════════
   THE LAST NOTE - ADMIN UTILITIES
   Helper functions and utilities for admin dashboard
   ═════════════════════════════════════════════════════════════════════════════*/

/**
 * Format currency value
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Calculate discount amount
 */
function calculateDiscount(price, discountType, discountValue) {
    if (!discountValue || discountValue === 0) return 0;
    
    if (discountType === 'percentage') {
        return (price * discountValue) / 100;
    } else if (discountType === 'fixed') {
        return discountValue;
    }
    
    return 0;
}

/**
 * Calculate final price
 */
function calculateFinalPrice(price, discountType, discountValue) {
    const discount = calculateDiscount(price, discountType, discountValue);
    return Math.max(0, price - discount);
}

/**
 * Validate discount value
 */
function validateDiscount(discountType, discountValue) {
    if (!discountValue || discountValue <= 0) {
        return { valid: false, error: 'Discount value must be greater than 0' };
    }
    
    if (discountType === 'percentage') {
        if (discountValue > 100) {
            return { valid: false, error: 'Percentage discount cannot exceed 100%' };
        }
    }
    
    return { valid: true };
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Get bearer token from localStorage
 */
function getBearerToken() {
    return localStorage.getItem('access_token');
}

/**
 * Create API headers
 */
function getApiHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getBearerToken()}`
    };
}

/**
 * Parse JWT token
 */
function parseJWT(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

/**
 * Check if user is admin
 */
function isUserAdmin() {
    const token = getBearerToken();
    if (!token) return false;
    
    const decoded = parseJWT(token);
    return decoded && decoded.user_type === 'admin';
}

/**
 * Generate random ID
 */
function generateId() {
    return '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Deep clone object
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Merge objects
 */
function mergeObjects(target, source) {
    return { ...target, ...source };
}

/**
 * Check if object is empty
 */
function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * Get form data as object
 */
function getFormData(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    
    for (let [key, value] of formData) {
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

/**
 * Show loading state on element
 */
function showLoadingState(element, text = 'Loading...') {
    element.disabled = true;
    element.dataset.originalText = element.textContent;
    element.textContent = '⏳ ' + text;
    element.classList.add('loading');
}

/**
 * Hide loading state on element
 */
function hideLoadingState(element) {
    element.disabled = false;
    element.textContent = element.dataset.originalText || 'Submit';
    element.classList.remove('loading');
}

/**
 * Animate element
 */
function animateElement(element, animationClass, duration = 300) {
    return new Promise((resolve) => {
        element.classList.add(animationClass);
        setTimeout(() => {
            element.classList.remove(animationClass);
            resolve();
        }, duration);
    });
}

/**
 * Scroll to element
 */
function scrollToElement(element, smooth = true) {
    element.scrollIntoView({
        behavior: smooth ? 'smooth' : 'auto',
        block: 'start'
    });
}

/**
 * Check network status
 */
function isOnline() {
    return navigator.onLine;
}

/**
 * Show notification
 */
function showNotification(title, options = {}) {
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            return new Notification(title, options);
        }
    }
}

/**
 * Request notification permission
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

/**
 * Export data as CSV
 */
function exportCSV(data, filename = 'export.csv') {
    const csv = [
        Object.keys(data[0]).join(','),
        ...data.map(row => Object.values(row).map(val => `"${val}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Export data as JSON
 */
function exportJSON(data, filename = 'export.json') {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Capitalize string
 */
function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
}

/**
 * Pluralize word
 */
function pluralize(word, count) {
    return count === 1 ? word : word + 's';
}

/**
 * Get query parameter
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Set query parameter
 */
function setQueryParam(param, value) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set(param, value);
    window.history.replaceState({}, '', `${window.location.pathname}?${urlParams}`);
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text)
        .then(() => true)
        .catch(() => false);
}

console.log('✅ Admin Utilities Loaded');
