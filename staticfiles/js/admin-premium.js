/* ═══════════════════════════════════════════════════════════════════════════════
   THE LAST NOTE - ADMIN PREMIUM FEATURES JS
   Version: 3.0 (Discounts, Offers, Limited Edition, Stock Management)
   ═════════════════════════════════════════════════════════════════════════════*/

class AdminPremiumFeatures {
    constructor() {
        this.discountManager = new DiscountManager();
        this.offerManager = new OfferManager();
        this.stockManager = new StockManager();
        this.tagsManager = new TagsManager();
        this.featureFlags = new FeatureFlags();
        
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.setupPricingCalculation();
        this.setupDiscountTypeChange();
        this.setupLimitedEditionToggle();
        this.setupStockStatusChange();
        this.setupTagsInput();
    }

    /* ═════════════════════════════════════════════════════════════════════
       DISCOUNT MANAGEMENT
       ═════════════════════════════════════════════════════════════════════*/

    attachEventListeners() {
        // Discount Type Change
        document.getElementById('fDiscountType')?.addEventListener('change', (e) => {
            this.onDiscountTypeChange(e.target.value);
        });

        // Discount Value Change
        document.getElementById('fDiscountValue')?.addEventListener('input', () => {
            this.updateFinalPrice();
        });

        // Price Change
        document.getElementById('fPrice')?.addEventListener('input', () => {
            this.updateFinalPrice();
        });

        // Stock Status Change
        document.getElementById('fStockStatus')?.addEventListener('change', (e) => {
            this.onStockStatusChange(e.target.value);
        });

        // Limited Edition Toggle
        document.getElementById('fIsLimitedEdition')?.addEventListener('change', (e) => {
            this.onLimitedEditionChange(e.target.checked);
        });
    }

    setupPricingCalculation() {
        // Listen to price and discount changes
        const priceInput = document.getElementById('fPrice');
        const discountInput = document.getElementById('fDiscountValue');
        
        if (priceInput) {
            priceInput.addEventListener('change', () => this.updateFinalPrice());
        }
        if (discountInput) {
            discountInput.addEventListener('change', () => this.updateFinalPrice());
        }
    }

    setupDiscountTypeChange() {
        const discountType = document.getElementById('fDiscountType');
        if (discountType) {
            discountType.addEventListener('change', (e) => {
                const type = e.target.value;
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
                        document.getElementById('fDiscountValue').max = 100;
                    } else {
                        hint.textContent = 'Discount amount ($)';
                        document.getElementById('fDiscountValue').max = '';
                    }
                }
            });
        }
    }

    updateFinalPrice() {
        const priceInput = document.getElementById('fPrice');
        const discountType = document.getElementById('fDiscountType');
        const discountValue = document.getElementById('fDiscountValue');
        const finalPriceDisplay = document.getElementById('finalPriceValue');

        if (!priceInput || !finalPriceDisplay) return;

        const price = parseFloat(priceInput.value) || 0;
        const type = discountType?.value || 'none';
        const discount = parseFloat(discountValue?.value) || 0;

        let finalPrice = price;

        if (type === 'percentage' && discount > 0) {
            finalPrice = price - (price * (discount / 100));
        } else if (type === 'fixed' && discount > 0) {
            finalPrice = Math.max(0, price - discount);
        }

        finalPriceDisplay.textContent = finalPrice.toFixed(2);
    }

    /* ═════════════════════════════════════════════════════════════════════
       LIMITED EDITION MANAGEMENT
       ═════════════════════════════════════════════════════════════════════*/

    setupLimitedEditionToggle() {
        const checkbox = document.getElementById('fIsLimitedEdition');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.onLimitedEditionChange(e.target.checked);
            });
        }
    }

    onLimitedEditionChange(isChecked) {
        const limitedQtyGroup = document.getElementById('limitedQtyGroup');
        if (limitedQtyGroup) {
            limitedQtyGroup.style.display = isChecked ? 'block' : 'none';
            if (!isChecked) {
                document.getElementById('fLimitedQty').value = '';
            }
        }
    }

    /* ═════════════════════════════════════════════════════════════════════
       STOCK STATUS MANAGEMENT
       ═════════════════════════════════════════════════════════════════════*/

    setupStockStatusChange() {
        const statusSelect = document.getElementById('fStockStatus');
        if (statusSelect) {
            statusSelect.addEventListener('change', (e) => {
                this.onStockStatusChange(e.target.value);
            });
        }
    }

    onStockStatusChange(status) {
        const preOrderGroup = document.getElementById('preOrderDateGroup');
        
        if (status === 'pre_order') {
            preOrderGroup.style.display = 'block';
        } else {
            preOrderGroup.style.display = 'none';
            if (document.getElementById('fPreOrderDate')) {
                document.getElementById('fPreOrderDate').value = '';
            }
        }
    }

    /* ═════════════════════════════════════════════════════════════════════
       TAGS MANAGEMENT
       ═════════════════════════════════════════════════════════════════════*/

    setupTagsInput() {
        const tagsInput = document.getElementById('fTags');
        if (tagsInput) {
            tagsInput.addEventListener('blur', () => {
                this.updateTagsDisplay();
            });
            tagsInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.updateTagsDisplay();
                }
            });
        }
    }

    updateTagsDisplay() {
        const tagsInput = document.getElementById('fTags');
        const tagsDisplay = document.getElementById('tagsDisplay');
        
        if (!tagsInput || !tagsDisplay) return;

        const tags = tagsInput.value
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);

        tagsDisplay.innerHTML = tags.map((tag, index) => `
            <div class="tag">
                <span>${tag}</span>
                <span class="tag-remove" onclick="removeTag(${index})">✕</span>
            </div>
        `).join('');
    }

    /* ═════════════════════════════════════════════════════════════════════
       GET FORM DATA (with premium fields)
       ═════════════════════════════════════════════════════════════════════*/

    static getFormDataWithPremium() {
        const baseData = formManager.getFormData();

        const premiumData = {
            // Discount Info
            discount_type: document.getElementById('fDiscountType')?.value || 'none',
            discount_value: parseFloat(document.getElementById('fDiscountValue')?.value) || 0,
            discount_start: document.getElementById('fDiscountStart')?.value || null,
            discount_end: document.getElementById('fDiscountEnd')?.value || null,
            cost_price: parseFloat(document.getElementById('fCostPrice')?.value) || 0,
            final_price: parseFloat(document.getElementById('finalPriceValue')?.textContent) || 0,

            // Limited Edition
            is_limited_edition: document.getElementById('fIsLimitedEdition')?.checked || false,
            limited_quantity: parseInt(document.getElementById('fLimitedQty')?.value) || 0,

            // Offers
            is_featured: document.getElementById('fIsFeatured')?.checked || false,
            is_hot_deal: document.getElementById('fIsHotDeal')?.checked || false,
            offer_description: document.getElementById('fOfferDescription')?.value || '',
            offer_end_date: document.getElementById('fOfferEndDate')?.value || null,

            // Stock Management
            stock_status: document.getElementById('fStockStatus')?.value || 'in_stock',
            low_stock_threshold: parseInt(document.getElementById('fLowStockThreshold')?.value) || 0,
            pre_order_date: document.getElementById('fPreOrderDate')?.value || null,
            allow_backorder: document.getElementById('fAllowBackorder')?.checked || false,
            reorder_level: parseInt(document.getElementById('fReorderLevel')?.value) || 0,
            warehouse: document.getElementById('fWarehouse')?.value || 'main',

            // Tags & Categories
            tags: document.getElementById('fTags')?.value.split(',').map(t => t.trim()).filter(t => t) || [],
            category: document.getElementById('fCategory')?.value || '',
            sub_category: document.getElementById('fSubCategory')?.value || '',
        };

        return { ...baseData, ...premiumData };
    }

    /* ═════════════════════════════════════════════════════════════════════
       PREFILL FORM WITH PREMIUM DATA
       ═════════════════════════════════════════════════════════════════════*/

    static prefillFormWithPremium(perfumeData) {
        // Base data
        formManager.setFormData(perfumeData);

        // Premium fields
        if (perfumeData.discount_type) {
            document.getElementById('fDiscountType').value = perfumeData.discount_type;
            document.querySelector('.premium-features').onDiscountTypeChange(perfumeData.discount_type);
        }

        if (perfumeData.discount_value) {
            document.getElementById('fDiscountValue').value = perfumeData.discount_value;
        }

        if (perfumeData.discount_start) {
            document.getElementById('fDiscountStart').value = perfumeData.discount_start;
        }

        if (perfumeData.discount_end) {
            document.getElementById('fDiscountEnd').value = perfumeData.discount_end;
        }

        if (perfumeData.cost_price) {
            document.getElementById('fCostPrice').value = perfumeData.cost_price;
        }

        // Limited Edition
        if (perfumeData.is_limited_edition) {
            document.getElementById('fIsLimitedEdition').checked = true;
            document.getElementById('limitedQtyGroup').style.display = 'block';
            if (perfumeData.limited_quantity) {
                document.getElementById('fLimitedQty').value = perfumeData.limited_quantity;
            }
        }

        // Offers
        if (perfumeData.is_featured) {
            document.getElementById('fIsFeatured').checked = true;
        }

        if (perfumeData.is_hot_deal) {
            document.getElementById('fIsHotDeal').checked = true;
        }

        if (perfumeData.offer_description) {
            document.getElementById('fOfferDescription').value = perfumeData.offer_description;
        }

        if (perfumeData.offer_end_date) {
            document.getElementById('fOfferEndDate').value = perfumeData.offer_end_date;
        }

        // Stock Management
        if (perfumeData.stock_status) {
            document.getElementById('fStockStatus').value = perfumeData.stock_status;
        }

        if (perfumeData.low_stock_threshold) {
            document.getElementById('fLowStockThreshold').value = perfumeData.low_stock_threshold;
        }

        if (perfumeData.pre_order_date) {
            document.getElementById('fPreOrderDate').value = perfumeData.pre_order_date;
        }

        if (perfumeData.allow_backorder) {
            document.getElementById('fAllowBackorder').checked = true;
        }

        if (perfumeData.reorder_level) {
            document.getElementById('fReorderLevel').value = perfumeData.reorder_level;
        }

        if (perfumeData.warehouse) {
            document.getElementById('fWarehouse').value = perfumeData.warehouse;
        }

        // Tags & Categories
        if (perfumeData.tags) {
            document.getElementById('fTags').value = Array.isArray(perfumeData.tags) 
                ? perfumeData.tags.join(', ')
                : perfumeData.tags;
        }

        if (perfumeData.category) {
            document.getElementById('fCategory').value = perfumeData.category;
        }

        if (perfumeData.sub_category) {
            document.getElementById('fSubCategory').value = perfumeData.sub_category;
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   DISCOUNT MANAGER CLASS
   ═════════════════════════════════════════════════════════════════════════════*/

class DiscountManager {
    validateDiscount(type, value, price) {
        if (type === 'none') return true;
        if (type === 'percentage' && (value < 0 || value > 100)) return false;
        if (type === 'fixed' && (value < 0 || value > price)) return false;
        return true;
    }

    calculateFinalPrice(price, type, value) {
        if (type === 'percentage') {
            return price * (1 - (value / 100));
        } else if (type === 'fixed') {
            return Math.max(0, price - value);
        }
        return price;
    }

    calculateProfitMargin(finalPrice, costPrice) {
        if (costPrice <= 0) return 0;
        return ((finalPrice - costPrice) / finalPrice) * 100;
    }

    validateDateRange(startDate, endDate) {
        if (!startDate || !endDate) return true;
        return new Date(startDate) < new Date(endDate);
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   OFFER MANAGER CLASS
   ═════════════════════════════════════════════════════════════════════════════*/

class OfferManager {
    createOffer(type, description, endDate) {
        return {
            type: type,
            description: description,
            end_date: endDate,
            created_at: new Date().toISOString(),
            is_active: new Date() < new Date(endDate)
        };
    }

    isOfferActive(offer) {
        if (!offer || !offer.end_date) return false;
        return new Date() < new Date(offer.end_date);
    }

    getOfferBadges(perfumeData) {
        const badges = [];
        
        if (perfumeData.is_limited_edition) {
            badges.push({
                text: '👑 Limited Edition',
                class: 'badge-limited-edition'
            });
        }

        if (perfumeData.is_featured) {
            badges.push({
                text: '⭐ Featured',
                class: 'badge-featured'
            });
        }

        if (perfumeData.is_hot_deal && this.isOfferActive(perfumeData.offer)) {
            badges.push({
                text: '🔥 Hot Deal',
                class: 'badge-hot-deal'
            });
        }

        if (perfumeData.discount_type !== 'none' && perfumeData.discount_value > 0) {
            let discountText = '';
            if (perfumeData.discount_type === 'percentage') {
                discountText = `💰 ${perfumeData.discount_value}% OFF`;
            } else {
                discountText = `💰 $${perfumeData.discount_value} OFF`;
            }
            badges.push({
                text: discountText,
                class: 'badge-discount'
            });
        }

        return badges;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   STOCK MANAGER CLASS
   ═════════════════════════════════════════════════════════════════════════════*/

class StockManager {
    getStockBadge(status, quantity, threshold) {
        switch (status) {
            case 'in_stock':
                return { text: '✅ In Stock', class: 'badge-stock-in' };
            case 'low_stock':
                return { text: `⚠️ Low Stock (${quantity})`, class: 'badge-stock-low' };
            case 'out_of_stock':
                return { text: '❌ Out of Stock', class: 'badge-stock-out' };
            case 'discontinued':
                return { text: '🛑 Discontinued', class: 'badge-discontinued' };
            case 'pre_order':
                return { text: '📅 Pre-Order', class: 'badge-pre-order' };
            default:
                return { text: status, class: 'badge' };
        }
    }

    updateStockStatus(quantity, threshold) {
        if (quantity === 0) return 'out_of_stock';
        if (quantity <= threshold) return 'low_stock';
        return 'in_stock';
    }

    shouldReorder(quantity, reorderLevel) {
        return quantity <= reorderLevel;
    }

    validateStockQuantity(quantity) {
        if (isNaN(quantity)) return false;
        return quantity >= 0;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   TAGS MANAGER CLASS
   ═════════════════════════════════════════════════════════════════════════════*/

class TagsManager {
    parseTags(tagString) {
        if (!tagString) return [];
        return tagString.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
    }

    formatTags(tags) {
        if (Array.isArray(tags)) return tags.join(', ');
        return tags || '';
    }

    validateTag(tag) {
        if (!tag || tag.trim().length === 0) return false;
        if (tag.length > 50) return false;
        return true;
    }

    getUniqueTagsFromProducts(products) {
        const allTags = new Set();
        products.forEach(product => {
            if (product.tags && Array.isArray(product.tags)) {
                product.tags.forEach(tag => allTags.add(tag));
            }
        });
        return Array.from(allTags).sort();
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   FEATURE FLAGS CLASS
   ═════════════════════════════════════════════════════════════════════════════*/

class FeatureFlags {
    constructor() {
        this.features = {
            discounts: true,
            limited_edition: true,
            offers: true,
            stock_management: true,
            tags: true,
            pre_order: true,
            backorder: true,
            hot_deal: true,
            featured_products: true
        };
    }

    isEnabled(featureName) {
        return this.features[featureName] || false;
    }

    enable(featureName) {
        this.features[featureName] = true;
    }

    disable(featureName) {
        this.features[featureName] = false;
    }

    getEnabledFeatures() {
        return Object.keys(this.features).filter(key => this.features[key]);
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   HELPER FUNCTIONS
   ═════════════════════════════════════════════════════════════════════════════*/

function removeTag(index) {
    const tagsInput = document.getElementById('fTags');
    const tags = tagsInput.value.split(',').map(t => t.trim());
    tags.splice(index, 1);
    tagsInput.value = tags.join(', ');
    
    // Re-render tags display
    const premiumFeatures = window.premiumFeatures;
    if (premiumFeatures) {
        premiumFeatures.updateTagsDisplay();
    }
}

function getStockStatusColor(status) {
    const colors = {
        'in_stock': '#10b981',
        'low_stock': '#f59e0b',
        'out_of_stock': '#ef4444',
        'discontinued': '#6b7280',
        'pre_order': '#3b82f6'
    };
    return colors[status] || '#9ca3af';
}

function getStockStatusIcon(status) {
    const icons = {
        'in_stock': '✅',
        'low_stock': '⚠️',
        'out_of_stock': '❌',
        'discontinued': '🛑',
        'pre_order': '📅'
    };
    return icons[status] || '📦';
}

/* ═══════════════════════════════════════════════════════════════════════════════
   INITIALIZE PREMIUM FEATURES
   ═════════════════════════════════════════════════════════════════════════════*/

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.premiumFeatures = new AdminPremiumFeatures();
    });
} else {
    window.premiumFeatures = new AdminPremiumFeatures();
}

/* ═══════════════════════════════════════════════════════════════════════════════
   END OF PREMIUM FEATURES JS
   ═════════════════════════════════════════════════════════════════════════════*/
