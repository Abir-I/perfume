/* ══════════════════════════════════════════════════════════════
   ADMIN FILTERS MODULE
   Manages advanced filtering for product list
   ══════════════════════════════════════════════════════════════ */

class AdminFilterManager {
  constructor() {
    this.filterBrand = document.getElementById('filterBrand');
    this.filterGender = document.getElementById('filterGender');
    this.filterType = document.getElementById('filterType');
    this.resetBtn = document.getElementById('resetFiltersBtn');
    this.searchInput = document.getElementById('adminSearchInput');

    this.activeFilters = {
      search: '',
      brand: '',
      gender: '',
      type: '',
    };

    this.init();
  }

  init() {
    // Filter change events
    if (this.filterBrand) {
      this.filterBrand.addEventListener('change', () => this.applyFilters());
    }
    if (this.filterGender) {
      this.filterGender.addEventListener('change', () => this.applyFilters());
    }
    if (this.filterType) {
      this.filterType.addEventListener('change', () => this.applyFilters());
    }

    // Reset button
    if (this.resetBtn) {
      this.resetBtn.addEventListener('click', () => this.resetFilters());
    }

    // Search input
    if (this.searchInput) {
      this.searchInput.addEventListener('input', () => this.applyFilters());
    }

    this.updateResetButtonVisibility();
  }

  applyFilters() {
    this.updateActiveFilters();
    this.updateResetButtonVisibility();

    // Trigger product load (from admin.js)
    if (typeof loadProducts === 'function') {
      loadProducts();
    }
  }

  updateActiveFilters() {
    this.activeFilters.search = this.searchInput?.value.trim() || '';
    this.activeFilters.brand = this.filterBrand?.value || '';
    this.activeFilters.gender = this.filterGender?.value || '';
    this.activeFilters.type = this.filterType?.value || '';
  }

  resetFilters() {
    if (this.searchInput) this.searchInput.value = '';
    if (this.filterBrand) this.filterBrand.value = '';
    if (this.filterGender) this.filterGender.value = '';
    if (this.filterType) this.filterType.value = '';

    this.activeFilters = {
      search: '',
      brand: '',
      gender: '',
      type: '',
    };

    this.updateResetButtonVisibility();

    // Trigger product load
    if (typeof loadProducts === 'function') {
      loadProducts();
    }

    // Show notification
    if (typeof showToast === 'function') {
      showToast('Filters cleared', 'info');
    }
  }

  updateResetButtonVisibility() {
    if (!this.resetBtn) return;

    const hasActiveFilters = 
      this.activeFilters.search || 
      this.activeFilters.brand || 
      this.activeFilters.gender || 
      this.activeFilters.type;

    if (hasActiveFilters) {
      this.resetBtn.style.display = 'inline-block';
      this.resetBtn.style.opacity = '1';
    } else {
      this.resetBtn.style.opacity = '0.4';
    }
  }

  getActiveFilterCount() {
    let count = 0;
    if (this.activeFilters.search) count++;
    if (this.activeFilters.brand) count++;
    if (this.activeFilters.gender) count++;
    if (this.activeFilters.type) count++;
    return count;
  }

  getFilterSummary() {
    const parts = [];
    if (this.activeFilters.search) parts.push(`Search: "${this.activeFilters.search}"`);
    if (this.activeFilters.brand) {
      const brandName = this.filterBrand?.querySelector(`option[value="${this.activeFilters.brand}"]`)?.textContent;
      if (brandName) parts.push(`Brand: ${brandName}`);
    }
    if (this.activeFilters.gender) {
      const genderName = this.filterGender?.querySelector(`option[value="${this.activeFilters.gender}"]`)?.textContent;
      if (genderName) parts.push(`Gender: ${genderName}`);
    }
    if (this.activeFilters.type) {
      const typeName = this.filterType?.querySelector(`option[value="${this.activeFilters.type}"]`)?.textContent;
      if (typeName) parts.push(`Type: ${typeName}`);
    }
    return parts.join(' • ');
  }

  // Utility: Update brand list dynamically
  updateBrandList(brands) {
    if (!this.filterBrand) return;

    const currentValue = this.filterBrand.value;
    this.filterBrand.innerHTML = '<option value="">All Brands</option>' +
      brands.map(b => `<option value="${b.brand_id}">${b.brand_name}</option>`).join('');
    this.filterBrand.value = currentValue;
  }
}

// Initialize filter manager when DOM is ready
let filterManager;
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('filterBrand')) {
    filterManager = new AdminFilterManager();
  }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AdminFilterManager;
}
