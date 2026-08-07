/* ═══════════════════════════════════════════════════════════════════════════════
   THE LAST NOTE - ADMIN PREMIUM DASHBOARD V4.0
   Comprehensive Admin Dashboard with Premium Features
   ═════════════════════════════════════════════════════════════════════════════*/

class AdminPremiumDashboard {
    constructor() {
        this.products = [];
        this.selectedProducts = new Set();
        this.currentEditingProduct = null;
        this.apiBaseUrl = '/api/catalog';  // Updated to match actual endpoint
        this.token = localStorage.getItem('access_token');
        this.isLoading = false;
        
        // Config
        this.config = {
            animationDuration: 300,
            toastDuration: 3000,
            debounceDelay: 300,
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardStats();
        this.loadProducts();
        this.setupFormHandlers();
        this.setupModalHandlers();
    }

    /* ═════════════════════════════════════════════════════════════════════
       API METHODS
       ═════════════════════════════════════════════════════════════════════*/

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                ...defaultOptions,
                ...options
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async loadDashboardStats() {
        try {
            const data = await this.apiCall('/admin/premium/stats/');
            this.updateStatsDisplay(data);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async loadProducts(filters = {}) {
        try {
            this.isLoading = true;
            const params = new URLSearchParams();
            
            if (filters.search) params.append('search', filters.search);
            if (filters.status) params.append('status', filters.status);
            if (filters.feature) params.append('feature', filters.feature);
            
            const url = `/admin/premium/products/?${params.toString()}`;
            const data = await this.apiCall(url);
            
            this.products = data.results || [];
            this.renderProducts();
        } catch (error) {
            console.error('Error loading products:', error);
            this.showToast('Failed to load products', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    async updateProduct(productId, data) {
        try {
            const response = await this.apiCall(`/products/${productId}/`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            
            this.showToast('Product updated successfully', 'success');
            this.loadProducts();
            return response;
        } catch (error) {
            console.error('Error updating product:', error);
            throw error;
        }
    }

    async updateDiscount(productId, discountData) {
        try {
            const response = await this.apiCall(`/admin/premium/products/${productId}/update-discount/`, {
                method: 'POST',
                body: JSON.stringify(discountData)
            });
            
            this.showToast('Discount updated successfully', 'success');
            this.loadProducts();
            return response;
        } catch (error) {
            console.error('Error updating discount:', error);
            throw error;
        }
    }

    async updateStock(productId, stockData) {
        try {
            const response = await this.apiCall(`/admin/premium/products/${productId}/update-stock/`, {
                method: 'POST',
                body: JSON.stringify(stockData)
            });
            
            this.showToast('Stock updated successfully', 'success');
            this.loadProducts();
            return response;
        } catch (error) {
            console.error('Error updating stock:', error);
            throw error;
        }
    }

    async updateFeatures(productId, featuresData) {
        try {
            const response = await this.apiCall(`/admin/premium/products/${productId}/update-features/`, {
                method: 'POST',
                body: JSON.stringify(featuresData)
            });
            
            this.showToast('Features updated successfully', 'success');
            this.loadProducts();
            return response;
        } catch (error) {
            console.error('Error updating features:', error);
            throw error;
        }
    }

    async bulkOperation(operation, productIds, value = null) {
        try {
            const data = {
                operation,
                product_ids: productIds,
            };
            
            if (value) data.value = value;
            
            const response = await this.apiCall('/admin/premium/bulk-operation/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.showToast(response.message, 'success');
            this.loadProducts();
            return response;
        } catch (error) {
            console.error('Error in bulk operation:', error);
            throw error;
        }
    }

    /* ═════════════════════════════════════════════════════════════════════
       UI METHODS - STATS & DISPLAY
       ═════════════════════════════════════════════════════════════════════*/

    updateStatsDisplay(stats) {
        document.getElementById('statTotalProducts').textContent = stats.total_products;
        document.getElementById('statInStock').textContent = stats.in_stock;
        document.getElementById('statLowStock').textContent = stats.low_stock;
        document.getElementById('statOutOfStock').textContent = stats.out_of_stock;
        document.getElementById('statOnDiscount').textContent = stats.on_discount;
        document.getElementById('statLimitedEdition').textContent = stats.limited_edition;
        
        // Update navbar stats
        document.getElementById('navStatsProducts').textContent = stats.total_products;
        document.getElementById('navStatsDiscounts').textContent = stats.on_discount;
    }

    renderProducts() {
        const tbody = document.getElementById('adminTableBody');
        
        if (this.products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 2rem;">No products found</td></tr>';
            document.getElementById('adminCount').textContent = '0 products';
            return;
        }

        tbody.innerHTML = this.products.map(product => this.createProductRow(product)).join('');
        document.getElementById('adminCount').textContent = `${this.products.length} products`;
        
        // Attach event listeners to action buttons
        this.attachProductRowListeners();
    }

    createProductRow(product) {
        const discountLabel = this.getDiscountLabel(product);
        const stockStatus = this.getStockStatus(product.stock_quantity);
        const features = this.getFeatureTags(product);
        
        return `
            <tr data-product-id="${product.product_id}">
                <td class="checkbox-col">
                    <input type="checkbox" class="product-checkbox" value="${product.product_id}">
                </td>
                <td><img src="${product.image_url}" alt="${product.perfume_name}"></td>
                <td>
                    <div class="product-name">${product.perfume_name}</div>
                    <div class="product-brand">${product.brand_name}</div>
                </td>
                <td>${product.brand_name}</td>
                <td class="price-cell">
                    <div>$${product.price.toFixed(2)}</div>
                    ${product.final_price !== product.price ? `<div style="color: #ef4444; font-weight: bold;">$${product.final_price.toFixed(2)}</div>` : ''}
                </td>
                <td>${discountLabel}</td>
                <td>
                    <span class="stock-status stock-${stockStatus.class}">
                        ${stockStatus.icon} ${product.stock_quantity}
                    </span>
                </td>
                <td>
                    <div class="features-cell">
                        ${features}
                    </div>
                </td>
                <td>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="admin-btn admin-btn-primary admin-btn-sm edit-btn" data-product-id="${product.product_id}">✎ Edit</button>
                        <button class="admin-btn admin-btn-secondary admin-btn-sm discount-btn" data-product-id="${product.product_id}">💰 Discount</button>
                        <button class="admin-btn admin-btn-danger admin-btn-sm delete-btn" data-product-id="${product.product_id}">🗑️ Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }

    getDiscountLabel(product) {
        if (product.discount_type === 'none' || !product.discount_value) {
            return '<span style="color: #64748b;">—</span>';
        }

        if (product.discount_type === 'percentage') {
            return `<span class="discount-badge">${product.discount_value}% OFF</span>`;
        } else {
            return `<span class="discount-badge">-$${product.discount_value.toFixed(2)}</span>`;
        }
    }

    getStockStatus(quantity) {
        if (quantity > 5) {
            return { class: 'in', icon: '✅' };
        } else if (quantity > 0) {
            return { class: 'low', icon: '⚠️' };
        } else {
            return { class: 'out', icon: '❌' };
        }
    }

    getFeatureTags(product) {
        const tags = [];
        
        if (product.is_featured) tags.push('<span class="feature-tag">⭐ Featured</span>');
        if (product.is_hot_deal) tags.push('<span class="feature-tag">🔥 Hot Deal</span>');
        if (product.is_limited_edition) tags.push(`<span class="feature-tag">👑 Limited (${product.limited_edition_qty})</span>`);
        if (!product.is_active) tags.push('<span class="feature-tag">🛑 Inactive</span>');
        
        return tags.length > 0 ? tags.join('') : '—';
    }

    /* ═════════════════════════════════════════════════════════════════════
       EVENT LISTENERS & HANDLERS
       ═════════════════════════════════════════════════════════════════════*/

    setupEventListeners() {
        // Search
        document.getElementById('adminSearchInput').addEventListener('input', 
            this.debounce(() => this.handleSearch(), this.config.debounceDelay)
        );

        // Filters
        document.getElementById('filterBrand').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterStatus').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterFeature').addEventListener('change', () => this.applyFilters());
        
        // Clear Filters
        document.getElementById('resetFiltersBtn').addEventListener('click', () => this.resetFilters());

        // Add Product
        document.getElementById('addPerfumeBtn').addEventListener('click', () => this.openProductModal());

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());

        // Select All checkbox
        document.getElementById('selectAllCheckbox').addEventListener('change', (e) => this.selectAllProducts(e.target.checked));
    }

    attachProductRowListeners() {
        // Product checkboxes
        document.querySelectorAll('.product-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const productId = parseInt(e.target.value);
                if (e.target.checked) {
                    this.selectedProducts.add(productId);
                } else {
                    this.selectedProducts.delete(productId);
                }
                this.updateBulkActionsPanel();
            });
        });

        // Edit buttons
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                this.openEditProductModal(productId);
            });
        });

        // Discount buttons
        document.querySelectorAll('.discount-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                this.openDiscountModal(productId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                this.confirmDelete(productId);
            });
        });
    }

    handleSearch() {
        const query = document.getElementById('adminSearchInput').value;
        this.applyFilters({ search: query });
    }

    applyFilters(overrides = {}) {
        const filters = {
            search: overrides.search !== undefined ? overrides.search : document.getElementById('adminSearchInput').value,
            status: document.getElementById('filterStatus').value,
            feature: document.getElementById('filterFeature').value,
        };

        this.loadProducts(filters);
    }

    resetFilters() {
        document.getElementById('adminSearchInput').value = '';
        document.getElementById('filterBrand').value = '';
        document.getElementById('filterStatus').value = '';
        document.getElementById('filterFeature').value = '';
        this.loadProducts();
    }

    selectAllProducts(checked) {
        if (checked) {
            this.products.forEach(p => this.selectedProducts.add(p.product_id));
        } else {
            this.selectedProducts.clear();
        }
        this.updateBulkActionsPanel();
    }

    updateBulkActionsPanel() {
        const panel = document.getElementById('bulkActionsPanel');
        const count = this.selectedProducts.size;

        if (count > 0) {
            panel.style.display = 'flex';
            document.getElementById('bulkSelectedCount').textContent = `${count} selected`;
        } else {
            panel.style.display = 'none';
            this.selectedProducts.clear();
        }
    }

    /* ═════════════════════════════════════════════════════════════════════
       MODAL HANDLERS
       ═════════════════════════════════════════════════════════════════════*/

    setupFormHandlers() {
        // Product Form
        document.getElementById('productForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProductFormSubmit();
        });

        // Discount Type Change
        document.getElementById('fDiscountType')?.addEventListener('change', (e) => {
            this.onDiscountTypeChange(e.target.value);
        });

        // Price and Discount Value Change
        document.getElementById('fPrice')?.addEventListener('input', () => this.updatePricePreview());
        document.getElementById('fDiscountValue')?.addEventListener('input', () => this.updatePricePreview());

        // Limited Edition Toggle
        document.getElementById('fIsLimitedEdition')?.addEventListener('change', (e) => {
            const group = document.getElementById('limitedQtyGroup');
            group.style.display = e.target.checked ? 'block' : 'none';
        });
    }

    setupModalHandlers() {
        // Product Modal
        document.getElementById('productModalClose').addEventListener('click', () => this.closeProductModal());
        document.getElementById('productFormCancel').addEventListener('click', () => this.closeProductModal());

        // Discount Modal
        document.getElementById('bulkDiscountClose').addEventListener('click', () => this.closeBulkDiscountModal());
        document.getElementById('bulkDiscountCancel').addEventListener('click', () => this.closeBulkDiscountModal());
        document.getElementById('bulkDiscountForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleBulkDiscountSubmit();
        });

        // Confirm Modal
        document.getElementById('confirmClose').addEventListener('click', () => this.closeConfirmModal());
        document.getElementById('confirmCancel').addEventListener('click', () => this.closeConfirmModal());

        // Close modals on outside click
        document.querySelectorAll('.admin-modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }

    openProductModal(productId = null) {
        const modal = document.getElementById('productModal');
        const form = document.getElementById('productForm');
        
        form.reset();
        this.currentEditingProduct = null;
        document.getElementById('productModalTitle').textContent = 'Add New Perfume';

        modal.classList.add('active');
    }

    openEditProductModal(productId) {
        const product = this.products.find(p => p.product_id === productId);
        if (!product) return;

        this.currentEditingProduct = product;
        const form = document.getElementById('productForm');

        // Fill form with product data
        document.getElementById('fPerfumeName').value = product.perfume_name;
        document.getElementById('fPrice').value = product.price;
        document.getElementById('fStock').value = product.stock_quantity;
        
        document.getElementById('fDiscountType').value = product.discount_type || 'none';
        document.getElementById('fDiscountValue').value = product.discount_value || '';
        document.getElementById('fDiscountStart').value = product.discount_start_date ? new Date(product.discount_start_date).toISOString().slice(0, 16) : '';
        document.getElementById('fDiscountEnd').value = product.discount_end_date ? new Date(product.discount_end_date).toISOString().slice(0, 16) : '';
        
        document.getElementById('fIsLimitedEdition').checked = product.is_limited_edition;
        document.getElementById('fLimitedQty').value = product.limited_edition_qty || 100;
        document.getElementById('fIsFeatured').checked = product.is_featured;
        document.getElementById('fIsHotDeal').checked = product.is_hot_deal;
        document.getElementById('fIsActive').checked = product.is_active;

        this.updatePricePreview();
        this.onDiscountTypeChange(product.discount_type || 'none');

        document.getElementById('productModalTitle').textContent = `Edit - ${product.perfume_name}`;
        document.getElementById('productModal').classList.add('active');
    }

    async handleProductFormSubmit() {
        if (!this.currentEditingProduct) {
            this.showToast('Feature coming soon: Add new products', 'info');
            this.closeProductModal();
            return;
        }

        const productId = this.currentEditingProduct.product_id;
        const formData = {
            discount_type: document.getElementById('fDiscountType').value,
            discount_value: parseFloat(document.getElementById('fDiscountValue').value) || 0,
            discount_start_date: document.getElementById('fDiscountStart').value ? new Date(document.getElementById('fDiscountStart').value).toISOString() : null,
            discount_end_date: document.getElementById('fDiscountEnd').value ? new Date(document.getElementById('fDiscountEnd').value).toISOString() : null,
            is_limited_edition: document.getElementById('fIsLimitedEdition').checked,
            limited_edition_qty: parseInt(document.getElementById('fLimitedQty').value) || 0,
            is_featured: document.getElementById('fIsFeatured').checked,
            is_hot_deal: document.getElementById('fIsHotDeal').checked,
            is_active: document.getElementById('fIsActive').checked,
            stock_quantity: parseInt(document.getElementById('fStock').value) || 0,
        };

        try {
            // Update discount
            await this.updateDiscount(productId, {
                discount_type: formData.discount_type,
                discount_value: formData.discount_value,
                discount_start_date: formData.discount_start_date,
                discount_end_date: formData.discount_end_date,
            });

            // Update stock
            await this.updateStock(productId, {
                stock_quantity: formData.stock_quantity,
                is_active: formData.is_active,
            });

            // Update features
            await this.updateFeatures(productId, {
                is_limited_edition: formData.is_limited_edition,
                limited_edition_qty: formData.limited_edition_qty,
                is_featured: formData.is_featured,
                is_hot_deal: formData.is_hot_deal,
            });

            this.closeProductModal();
        } catch (error) {
            this.showToast('Error saving product', 'error');
        }
    }

    openDiscountModal(productId) {
        const product = this.products.find(p => p.product_id === productId);
        if (!product) return;

        document.getElementById('bulkDiscountForm').dataset.productId = productId;
        document.getElementById('bulkDiscountType').value = product.discount_type || 'percentage';
        document.getElementById('bulkDiscountValue').value = product.discount_value || '';

        document.getElementById('bulkDiscountModal').classList.add('active');
    }

    async handleBulkDiscountSubmit() {
        const productId = parseInt(document.getElementById('bulkDiscountForm').dataset.productId);
        const type = document.getElementById('bulkDiscountType').value;
        const value = parseFloat(document.getElementById('bulkDiscountValue').value);

        if (isNaN(value) || value < 0) {
            this.showToast('Invalid discount value', 'error');
            return;
        }

        try {
            await this.updateDiscount(productId, {
                discount_type: type,
                discount_value: value,
            });
            this.closeBulkDiscountModal();
        } catch (error) {
            this.showToast('Error updating discount', 'error');
        }
    }

    closeProductModal() {
        document.getElementById('productModal').classList.remove('active');
        this.currentEditingProduct = null;
    }

    closeBulkDiscountModal() {
        document.getElementById('bulkDiscountModal').classList.remove('active');
    }

    closeConfirmModal() {
        document.getElementById('confirmModal').classList.remove('active');
    }

    async confirmDelete(productId) {
        this.showConfirm(
            'Delete Product',
            'Are you sure you want to delete this product? This action cannot be undone.',
            () => this.handleDelete(productId)
        );
    }

    async handleDelete(productId) {
        this.showToast('Delete feature coming soon', 'info');
    }

    /* ═════════════════════════════════════════════════════════════════════
       UTILITY METHODS
       ═════════════════════════════════════════════════════════════════════*/

    onDiscountTypeChange(type) {
        const valueGroup = document.getElementById('discountValueGroup');
        const startGroup = document.getElementById('discountStartGroup');
        const endGroup = document.getElementById('discountEndGroup');
        const hint = document.getElementById('discountHint');

        if (type === 'none') {
            valueGroup.style.display = 'none';
            startGroup.style.display = 'none';
            endGroup.style.display = 'none';
        } else {
            valueGroup.style.display = 'block';
            startGroup.style.display = 'block';
            endGroup.style.display = 'block';

            if (type === 'percentage') {
                hint.textContent = 'Discount percentage (0-100)';
                document.getElementById('fDiscountValue').max = '100';
            } else {
                hint.textContent = 'Discount amount ($)';
                document.getElementById('fDiscountValue').max = '';
            }
        }
    }

    updatePricePreview() {
        const price = parseFloat(document.getElementById('fPrice').value) || 0;
        const type = document.getElementById('fDiscountType').value;
        const discount = parseFloat(document.getElementById('fDiscountValue').value) || 0;

        let finalPrice = price;

        if (type === 'percentage' && discount > 0) {
            finalPrice = price * (1 - discount / 100);
        } else if (type === 'fixed' && discount > 0) {
            finalPrice = Math.max(0, price - discount);
        }

        document.getElementById('origPricePreview').textContent = `$${price.toFixed(2)}`;
        document.getElementById('finalPricePreview').textContent = `$${finalPrice.toFixed(2)}`;
    }

    handleLogout() {
        localStorage.removeItem('access_token');
        window.location.href = '/';
    }

    /* ═════════════════════════════════════════════════════════════════════
       UI FEEDBACK
       ═════════════════════════════════════════════════════════════════════*/

    showToast(message, type = 'info') {
        const toast = document.getElementById('adminToast');
        const toastMessage = document.getElementById('toastMessage');

        toastMessage.textContent = message;
        toast.className = `admin-toast show ${type}`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, this.config.toastDuration);
    }

    showConfirm(title, message, onConfirm) {
        const modal = document.getElementById('confirmModal');
        document.getElementById('confirmTitle').textContent = title;
        document.getElementById('confirmMessage').textContent = message;

        document.getElementById('confirmOk').onclick = () => {
            onConfirm();
            this.closeConfirmModal();
        };

        modal.classList.add('active');
    }

    debounce(func, wait) {
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
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.adminDashboard = new AdminPremiumDashboard();
    });
} else {
    window.adminDashboard = new AdminPremiumDashboard();
}
