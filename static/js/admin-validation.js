/* ═══════════════════════════════════════════════════════════════════════════════
   VALIDATION RULES - PREMIUM EDITION
   Includes all premium features: discounts, offers, limited edition, stock management
   ═════════════════════════════════════════════════════════════════════════════*/

const PremiumValidationRules = {
    /* Base Product Fields */
    perfume_name: {
        required: true,
        type: 'string',
        minLength: 2,
        maxLength: 100,
        pattern: /^[a-zA-Z0-9\s\-'()&]+$/,
        errorMessages: {
            required: 'Product name is required',
            minLength: 'Name must be at least 2 characters',
            maxLength: 'Name must not exceed 100 characters',
            pattern: 'Name contains invalid characters'
        }
    },

    brand_id: {
        required: true,
        type: 'number',
        errorMessages: {
            required: 'Please select a brand',
            type: 'Brand must be a number'
        }
    },

    concentration: {
        required: true,
        type: 'string',
        allowedValues: ['EDT', 'EDP', 'Parfum', 'EDC', 'Cologne'],
        errorMessages: {
            required: 'Concentration is required',
            type: 'Concentration must be a string',
            allowedValues: 'Please select a valid concentration'
        }
    },

    target_gender: {
        required: true,
        type: 'string',
        allowedValues: ['Male', 'Female', 'Unisex'],
        errorMessages: {
            required: 'Target gender is required',
            allowedValues: 'Please select Male, Female, or Unisex'
        }
    },

    product_type: {
        required: true,
        type: 'string',
        allowedValues: ['Decant', 'full_bottle'],
        errorMessages: {
            required: 'Product type is required',
            allowedValues: 'Please select Decant or Full Bottle'
        }
    },

    volume_ml: {
        required: true,
        type: 'number',
        min: 0.5,
        max: 500,
        errorMessages: {
            required: 'Volume is required',
            type: 'Volume must be a number',
            min: 'Volume must be at least 0.5 ml',
            max: 'Volume must not exceed 500 ml'
        }
    },

    price: {
        required: true,
        type: 'number',
        min: 0.01,
        max: 99999,
        errorMessages: {
            required: 'Price is required',
            type: 'Price must be a number',
            min: 'Price must be greater than 0',
            max: 'Price exceeds maximum allowed'
        }
    },

    stock_quantity: {
        type: 'number',
        min: 0,
        errorMessages: {
            type: 'Stock must be a number',
            min: 'Stock cannot be negative'
        }
    },

    description: {
        type: 'string',
        maxLength: 500,
        errorMessages: {
            type: 'Description must be text',
            maxLength: 'Description must not exceed 500 characters'
        }
    },

    /* ═════════════════════════════════════════════════════════════════════
       PREMIUM FEATURE FIELDS - DISCOUNTS
       ═════════════════════════════════════════════════════════════════════*/

    discount_type: {
        type: 'string',
        allowedValues: ['none', 'percentage', 'fixed'],
        errorMessages: {
            type: 'Discount type must be a string',
            allowedValues: 'Invalid discount type'
        }
    },

    discount_value: {
        type: 'number',
        min: 0,
        conditional: {
            when: 'discount_type',
            notEqual: 'none',
            errorMessages: {
                type: 'Discount value must be a number',
                min: 'Discount cannot be negative',
                conditional: 'Please enter a discount value'
            }
        },
        customValidation: function(value, formData) {
            const type = formData.discount_type;
            if (type === 'percentage' && (value < 0 || value > 100)) {
                return { valid: false, message: 'Percentage discount must be between 0-100' };
            }
            if (type === 'fixed' && value > formData.price) {
                return { valid: false, message: 'Fixed discount cannot exceed price' };
            }
            return { valid: true };
        },
        errorMessages: {
            type: 'Discount value must be a number',
            min: 'Discount cannot be negative',
            customValidation: 'Invalid discount value'
        }
    },

    discount_start: {
        type: 'datetime',
        conditional: {
            when: 'discount_type',
            notEqual: 'none'
        },
        customValidation: function(value, formData) {
            if (!value && formData.discount_type !== 'none') {
                return { valid: false, message: 'Discount start date is required when discount is active' };
            }
            if (value && new Date(value) < new Date()) {
                return { valid: false, message: 'Start date cannot be in the past' };
            }
            return { valid: true };
        }
    },

    discount_end: {
        type: 'datetime',
        conditional: {
            when: 'discount_type',
            notEqual: 'none'
        },
        customValidation: function(value, formData) {
            if (!value && formData.discount_type !== 'none') {
                return { valid: false, message: 'Discount end date is required when discount is active' };
            }
            if (value && formData.discount_start && new Date(value) <= new Date(formData.discount_start)) {
                return { valid: false, message: 'End date must be after start date' };
            }
            return { valid: true };
        }
    },

    cost_price: {
        type: 'number',
        min: 0,
        errorMessages: {
            type: 'Cost price must be a number',
            min: 'Cost price cannot be negative'
        }
    },

    /* ═════════════════════════════════════════════════════════════════════
       PREMIUM FEATURE FIELDS - LIMITED EDITION
       ═════════════════════════════════════════════════════════════════════*/

    is_limited_edition: {
        type: 'boolean',
        errorMessages: {
            type: 'Must be yes or no'
        }
    },

    limited_quantity: {
        type: 'number',
        min: 1,
        conditional: {
            when: 'is_limited_edition',
            equal: true
        },
        customValidation: function(value, formData) {
            if (formData.is_limited_edition && (!value || value < 1)) {
                return { valid: false, message: 'Limited quantity is required for limited edition products' };
            }
            return { valid: true };
        },
        errorMessages: {
            type: 'Limited quantity must be a number',
            min: 'Quantity must be at least 1',
            customValidation: 'Invalid quantity'
        }
    },

    /* ═════════════════════════════════════════════════════════════════════
       PREMIUM FEATURE FIELDS - OFFERS
       ═════════════════════════════════════════════════════════════════════*/

    is_featured: {
        type: 'boolean',
        errorMessages: {
            type: 'Must be yes or no'
        }
    },

    is_hot_deal: {
        type: 'boolean',
        errorMessages: {
            type: 'Must be yes or no'
        }
    },

    offer_description: {
        type: 'string',
        maxLength: 200,
        conditional: {
            when: 'is_hot_deal',
            equal: true
        },
        errorMessages: {
            type: 'Offer description must be text',
            maxLength: 'Description must not exceed 200 characters'
        }
    },

    offer_end_date: {
        type: 'datetime',
        conditional: {
            when: 'is_hot_deal',
            equal: true
        },
        customValidation: function(value, formData) {
            if (formData.is_hot_deal && !value) {
                return { valid: false, message: 'Offer end date is required for hot deals' };
            }
            if (value && new Date(value) < new Date()) {
                return { valid: false, message: 'Offer end date cannot be in the past' };
            }
            return { valid: true };
        }
    },

    /* ═════════════════════════════════════════════════════════════════════
       PREMIUM FEATURE FIELDS - STOCK MANAGEMENT
       ═════════════════════════════════════════════════════════════════════*/

    stock_status: {
        type: 'string',
        allowedValues: ['in_stock', 'low_stock', 'out_of_stock', 'discontinued', 'pre_order'],
        errorMessages: {
            type: 'Stock status must be a string',
            allowedValues: 'Please select a valid stock status'
        }
    },

    low_stock_threshold: {
        type: 'number',
        min: 0,
        errorMessages: {
            type: 'Threshold must be a number',
            min: 'Threshold cannot be negative'
        }
    },

    pre_order_date: {
        type: 'datetime',
        conditional: {
            when: 'stock_status',
            equal: 'pre_order'
        },
        customValidation: function(value, formData) {
            if (formData.stock_status === 'pre_order' && !value) {
                return { valid: false, message: 'Pre-order date is required when status is pre-order' };
            }
            if (value && new Date(value) <= new Date()) {
                return { valid: false, message: 'Pre-order date must be in the future' };
            }
            return { valid: true };
        }
    },

    allow_backorder: {
        type: 'boolean',
        errorMessages: {
            type: 'Must be yes or no'
        }
    },

    reorder_level: {
        type: 'number',
        min: 0,
        errorMessages: {
            type: 'Reorder level must be a number',
            min: 'Reorder level cannot be negative'
        }
    },

    warehouse: {
        type: 'string',
        allowedValues: ['main', 'secondary', 'online_only'],
        errorMessages: {
            type: 'Warehouse must be a string',
            allowedValues: 'Please select a valid warehouse'
        }
    },

    /* ═════════════════════════════════════════════════════════════════════
       PREMIUM FEATURE FIELDS - TAGS & CATEGORIES
       ═════════════════════════════════════════════════════════════════════*/

    tags: {
        type: 'array',
        maxItems: 10,
        itemMaxLength: 50,
        customValidation: function(value, formData) {
            if (!Array.isArray(value)) {
                return { valid: false, message: 'Tags must be an array' };
            }
            if (value.length > 10) {
                return { valid: false, message: 'Maximum 10 tags allowed' };
            }
            for (let tag of value) {
                if (tag.length > 50) {
                    return { valid: false, message: 'Each tag must be 50 characters or less' };
                }
            }
            return { valid: true };
        },
        errorMessages: {
            type: 'Tags must be an array',
            maxItems: 'Maximum 10 tags allowed',
            customValidation: 'Invalid tags'
        }
    },

    category: {
        type: 'string',
        allowedValues: ['luxury', 'fresh', 'floral', 'oriental', 'woody', 'fruity', 'aromatic'],
        errorMessages: {
            type: 'Category must be a string',
            allowedValues: 'Please select a valid category'
        }
    },

    sub_category: {
        type: 'string',
        errorMessages: {
            type: 'Sub-category must be a string'
        }
    },
};

/* ═══════════════════════════════════════════════════════════════════════════════
   ENHANCED FORM VALIDATOR
   ═════════════════════════════════════════════════════════════════════════════*/

class PremiumFormValidator {
    validate(fieldName, value, formData = {}) {
        const rule = PremiumValidationRules[fieldName];
        
        if (!rule) {
            return { valid: true, message: '' };
        }

        // Required validation
        if (rule.required && (value === undefined || value === null || value === '')) {
            return { valid: false, message: rule.errorMessages.required };
        }

        // Skip further validation if value is empty and not required
        if (!rule.required && (value === undefined || value === null || value === '')) {
            return { valid: true, message: '' };
        }

        // Type validation
        if (rule.type && !this.validateType(value, rule.type)) {
            return { valid: false, message: rule.errorMessages.type };
        }

        // Allowed values
        if (rule.allowedValues && !rule.allowedValues.includes(value)) {
            return { valid: false, message: rule.errorMessages.allowedValues };
        }

        // Min/Max for numbers
        if (rule.type === 'number') {
            if (rule.min !== undefined && value < rule.min) {
                return { valid: false, message: rule.errorMessages.min };
            }
            if (rule.max !== undefined && value > rule.max) {
                return { valid: false, message: rule.errorMessages.max };
            }
        }

        // Min/Max length for strings
        if (rule.type === 'string') {
            if (rule.minLength && value.length < rule.minLength) {
                return { valid: false, message: rule.errorMessages.minLength };
            }
            if (rule.maxLength && value.length > rule.maxLength) {
                return { valid: false, message: rule.errorMessages.maxLength };
            }
            if (rule.pattern && !rule.pattern.test(value)) {
                return { valid: false, message: rule.errorMessages.pattern };
            }
        }

        // Conditional validation
        if (rule.conditional) {
            const condition = rule.conditional;
            const fieldValue = formData[condition.when];
            
            let conditionMet = false;
            if (condition.equal !== undefined) {
                conditionMet = fieldValue === condition.equal;
            } else if (condition.notEqual !== undefined) {
                conditionMet = fieldValue !== condition.notEqual;
            }

            if (conditionMet && !value) {
                return { valid: false, message: condition.errorMessages.conditional };
            }
        }

        // Custom validation
        if (rule.customValidation && typeof rule.customValidation === 'function') {
            const result = rule.customValidation(value, formData);
            if (!result.valid) {
                return result;
            }
        }

        return { valid: true, message: '' };
    }

    validateType(value, expectedType) {
        switch (expectedType) {
            case 'string':
                return typeof value === 'string';
            case 'number':
                return !isNaN(value) && isFinite(value);
            case 'boolean':
                return typeof value === 'boolean';
            case 'datetime':
                return !isNaN(new Date(value).getTime());
            case 'array':
                return Array.isArray(value);
            default:
                return true;
        }
    }

    validateForm(formData) {
        const errors = {};
        
        Object.keys(PremiumValidationRules).forEach(fieldName => {
            const result = this.validate(fieldName, formData[fieldName], formData);
            if (!result.valid) {
                errors[fieldName] = result.message;
            }
        });

        return {
            isValid: Object.keys(errors).length === 0,
            errors: errors
        };
    }

    getFirstError(formData) {
        const result = this.validateForm(formData);
        if (!result.isValid) {
            const firstErrorKey = Object.keys(result.errors)[0];
            return {
                field: firstErrorKey,
                message: result.errors[firstErrorKey]
            };
        }
        return null;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   HELPER FUNCTIONS FOR FORM VALIDATION DISPLAY
   ═════════════════════════════════════════════════════════════════════════════*/

function addPremiumFieldValidation(fieldElement, isValid, message) {
    if (!fieldElement) return;

    const group = fieldElement.closest('.form-group');
    if (!group) return;

    // Remove existing error
    const existingError = group.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }

    if (!isValid && message) {
        fieldElement.classList.add('form-input-error');
        const errorEl = document.createElement('span');
        errorEl.className = 'form-error';
        errorEl.textContent = message;
        group.appendChild(errorEl);
    } else {
        fieldElement.classList.remove('form-input-error');
    }
}

function clearPremiumFieldValidation(fieldElement) {
    if (!fieldElement) return;

    const group = fieldElement.closest('.form-group');
    if (!group) return;

    fieldElement.classList.remove('form-input-error');
    const errorEl = group.querySelector('.form-error');
    if (errorEl) {
        errorEl.remove();
    }
}

/* ═══════════════════════════════════════════════════════════════════════════════
   EXPORT FOR USE IN OTHER MODULES
   ═════════════════════════════════════════════════════════════════════════════*/

// Make validator available globally
window.premiumValidator = new PremiumFormValidator();

/* ═══════════════════════════════════════════════════════════════════════════════
   END OF PREMIUM VALIDATION RULES
   ═════════════════════════════════════════════════════════════════════════════*/
