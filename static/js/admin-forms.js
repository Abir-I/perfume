/* ══════════════════════════════════════════════════════════════
   ADMIN FORMS MODULE
   Handles form initialization, field management, and validation
   ══════════════════════════════════════════════════════════════ */

class AdminFormManager {
  constructor() {
    this.form = document.getElementById('perfumeForm');
    this.fields = {
      brand: document.getElementById('fBrand'),
      name: document.getElementById('fName'),
      concentration: document.getElementById('fConcentration'),
      gender: document.getElementById('fGender'),
      longevity: document.getElementById('fLongevity'),
      season: document.getElementById('fSeason'),
      topNotes: document.getElementById('fTopNotes'),
      middleNotes: document.getElementById('fMiddleNotes'),
      baseNotes: document.getElementById('fBaseNotes'),
      description: document.getElementById('fDescription'),
      productType: document.getElementById('fProductType'),
      volume: document.getElementById('fVolume'),
      price: document.getElementById('fPrice'),
      stock: document.getElementById('fStock'),
    };
    this.errorDisplay = document.getElementById('perfumeFormError');
    this.initFieldValidation();
  }

  initFieldValidation() {
    // Real-time validation on blur
    Object.keys(this.fields).forEach(key => {
      const field = this.fields[key];
      if (field) {
        field.addEventListener('blur', (e) => this.validateField(e.target));
        field.addEventListener('change', (e) => this.clearFieldError(e.target));
      }
    });

    // Description character count
    if (this.fields.description) {
      this.fields.description.addEventListener('input', (e) => {
        this.updateCharCount(e.target.value.length);
      });
    }
  }

  validateField(field) {
    this.clearFieldError(field);

    const value = field.value.trim();
    const fieldName = field.id;

    // Required fields
    if (field.hasAttribute('required')) {
      if (!value) {
        this.setFieldError(field, 'This field is required');
        return false;
      }
    }

    // Number fields
    if (field.type === 'number') {
      const numValue = Number(value);

      if (fieldName === 'fPrice' && numValue <= 0) {
        this.setFieldError(field, 'Price must be greater than 0');
        return false;
      }

      if (fieldName === 'fVolume' && numValue <= 0) {
        this.setFieldError(field, 'Volume must be greater than 0');
        return false;
      }

      if (fieldName === 'fLongevity' && numValue > 24) {
        this.setFieldError(field, 'Longevity cannot exceed 24 hours');
        return false;
      }

      if (fieldName === 'fStock' && numValue < 0) {
        this.setFieldError(field, 'Stock cannot be negative');
        return false;
      }
    }

    // Text length
    if (fieldName === 'fName' && value.length > 100) {
      this.setFieldError(field, 'Name cannot exceed 100 characters');
      return false;
    }

    return true;
  }

  setFieldError(field, message) {
    field.classList.add('error');
    const hint = field.parentElement?.querySelector('.admin-form-hint');
    if (hint) {
      hint.textContent = message;
      hint.style.color = '#DC2626';
    }
  }

  clearFieldError(field) {
    field.classList.remove('error');
    const hint = field.parentElement?.querySelector('.admin-form-hint');
    if (hint && !hint.dataset.originalText) {
      hint.dataset.originalText = hint.textContent;
    }
  }

  updateCharCount(count) {
    const charCount = document.getElementById('charCount');
    if (charCount) {
      charCount.textContent = count;
      // Change color if too long
      if (count > 500) {
        charCount.style.color = '#DC2626';
      } else {
        charCount.style.color = '';
      }
    }
  }

  getFormData() {
    return {
      brand_id: this.fields.brand.value,
      perfume_name: this.fields.name.value.trim(),
      concentration: this.fields.concentration.value,
      target_gender: this.fields.gender.value,
      longevity_hours: this.fields.longevity.value || '0',
      recommended_season: this.fields.season.value || '',
      top_notes: this.fields.topNotes.value.trim() || '',
      middle_notes: this.fields.middleNotes.value.trim() || '',
      base_notes: this.fields.baseNotes.value.trim() || '',
      description: this.fields.description.value.trim() || '',
      product_type: this.fields.productType.value,
      volume_ml: this.fields.volume.value,
      price: this.fields.price.value,
      stock_quantity: this.fields.stock.value || '0',
    };
  }

  setFormData(data) {
    if (data.brand_id) this.fields.brand.value = data.brand_id;
    if (data.perfume_name) this.fields.name.value = data.perfume_name;
    if (data.concentration) this.fields.concentration.value = data.concentration;
    if (data.target_gender) this.fields.gender.value = data.target_gender;
    if (data.longevity_hours) this.fields.longevity.value = data.longevity_hours;
    if (data.recommended_season) this.fields.season.value = data.recommended_season;
    if (data.top_notes) this.fields.topNotes.value = data.top_notes;
    if (data.middle_notes) this.fields.middleNotes.value = data.middle_notes;
    if (data.base_notes) this.fields.baseNotes.value = data.base_notes;
    if (data.description) {
      this.fields.description.value = data.description;
      this.updateCharCount(data.description.length);
    }
    if (data.product_type) this.fields.productType.value = data.product_type;
    if (data.volume_ml) this.fields.volume.value = data.volume_ml;
    if (data.price) this.fields.price.value = data.price;
    if (data.stock_quantity) this.fields.stock.value = data.stock_quantity;
  }

  reset() {
    this.form.reset();
    Object.keys(this.fields).forEach(key => {
      this.clearFieldError(this.fields[key]);
    });
    this.errorDisplay.classList.remove('show');
    this.updateCharCount(0);
  }

  showError(message) {
    this.errorDisplay.textContent = message;
    this.errorDisplay.classList.add('show');
    // Scroll to error
    this.errorDisplay.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  hideError() {
    this.errorDisplay.classList.remove('show');
  }

  validateAllFields() {
    const requiredFields = ['fBrand', 'fName', 'fConcentration', 'fGender', 'fProductType', 'fVolume', 'fPrice'];
    let isValid = true;

    requiredFields.forEach(fieldId => {
      const field = document.getElementById(fieldId);
      if (field && !this.validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }
}

// Initialize form manager when DOM is ready
let formManager;
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('perfumeForm')) {
    formManager = new AdminFormManager();
  }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AdminFormManager;
}
