/**
 * Nepal Meat Shop - Main JavaScript File
 * Handles frontend interactions and functionality
 */

// Global variables
let cartUpdateTimeout;
let notificationTimeout;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeCartButtons();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('🍖 Nepal Meat Shop - Application Initialized');
    
    // Initialize components
    initializeNavigation();
    initializeCart();
    initializeForms();
    initializeModals();
    initializeTooltips();
    initializeAnimations();
    initializeQuantitySelector();
    
    // Set up event listeners
    setupEventListeners();
    
    // Update cart badge
    updateCartBadge();
    
    // Initialize any page-specific functionality
    initializePageSpecific();
}

/**
 * Initialize navigation functionality
 */
function initializeNavigation() {
    // Mobile menu handling
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            setTimeout(() => {
                if (navbarCollapse.classList.contains('show')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            }, 100);
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navbarCollapse && navbarCollapse.classList.contains('show') && 
            !navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
            const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                toggle: false
            });
            bsCollapse.hide();
            document.body.style.overflow = '';
        }
    });
    
    // Active link highlighting
    highlightActiveNavLink();
}

/**
 * Highlight active navigation link
 */
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

/**
 * Initialize cart functionality
 */
function initializeCart() {
    // Cart quantity controls
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateQuantity(this);
        });
        
        input.addEventListener('input', function() {
            clearTimeout(cartUpdateTimeout);
            cartUpdateTimeout = setTimeout(() => {
                validateQuantity(this);
            }, 500);
        });
    });
    
    // Add to cart buttons
    const addToCartForms = document.querySelectorAll('form[action*="add_to_cart"]');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Remove from cart confirmation
    const removeFromCartForms = document.querySelectorAll('form[action*="remove_from_cart"]');
    removeFromCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const productName = this.closest('.card, .cart-item').querySelector('.product-name, h6')?.textContent || 'this item';
            
            showConfirmDialog(
                'Remove Item',
                `Are you sure you want to remove "${productName}" from your cart?`,
                'Remove',
                'btn-danger'
            ).then(confirmed => {
                if (confirmed) {
                    this.submit();
                }
            });
        });
    });
}

/**
 * Initialize quantity selector functionality
 */
function initializeQuantitySelector() {
    const quantitySelectors = document.querySelectorAll('.quantity-selector');
    
    quantitySelectors.forEach(selector => {
        const input = selector.querySelector('.quantity-input');
        const decreaseBtn = selector.querySelector('[data-action="decrease"]');
        const increaseBtn = selector.querySelector('[data-action="increase"]');
        
        if (!input || !decreaseBtn || !increaseBtn) return;
        
        const min = parseFloat(input.getAttribute('min')) || 0.5;
        const max = parseFloat(input.getAttribute('max')) || 999;
        const step = parseFloat(input.getAttribute('step')) || 0.5;
        
        // Get price elements
        const totalPriceElement = document.querySelector('.total-price');
        const quantityDisplayElement = document.querySelector('.quantity-display');
        const totalPriceSection = document.querySelector('.total-price-section');
        
        let unitPrice = 0;
        if (totalPriceElement) {
            unitPrice = parseFloat(totalPriceElement.getAttribute('data-unit-price')) || 0;
        }
        
        // Set initial value if empty
        if (!input.value || parseFloat(input.value) < min) {
            input.value = min.toFixed(1);
        }
        
        // Update price display
        function updatePriceDisplay() {
            if (!totalPriceElement || !quantityDisplayElement || !totalPriceSection) return;
            
            const quantity = parseFloat(input.value) || min;
            const totalPrice = unitPrice * quantity;
            
            // Show total price section when quantity selector is used
            if (totalPriceSection.style.display === 'none') {
                totalPriceSection.style.display = 'block';
            }
            
            // Add animation class
            totalPriceElement.classList.add('updating');
            
            // Update values
            totalPriceElement.textContent = `रू ${Math.round(totalPrice).toLocaleString('en-IN')}`;
            quantityDisplayElement.textContent = quantity.toFixed(1);
            
            // Add price update animation
            totalPriceElement.classList.add('price-update-animation');
            
            // Remove animation classes after animation completes
            setTimeout(() => {
                totalPriceElement.classList.remove('updating', 'price-update-animation');
            }, 300);
        }
        
        // Update button states
        function updateButtonStates() {
            const currentValue = parseFloat(input.value) || min;
            decreaseBtn.disabled = currentValue <= min;
            increaseBtn.disabled = currentValue >= max;
            updatePriceDisplay();
        }
        
        // Decrease quantity
        decreaseBtn.addEventListener('click', function() {
            const currentValue = parseFloat(input.value) || min;
            const newValue = Math.max(min, currentValue - step);
            
            if (newValue >= min) {
                input.value = newValue.toFixed(1);
                updateButtonStates();
                
                // Add visual feedback
                this.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            } else {
                showToast(`Minimum quantity is ${min} kg`, 'warning');
            }
        });
        
        // Increase quantity
        increaseBtn.addEventListener('click', function() {
            const currentValue = parseFloat(input.value) || min;
            const newValue = Math.min(max, currentValue + step);
            
            if (newValue <= max) {
                input.value = newValue.toFixed(1);
                updateButtonStates();
                
                // Add visual feedback
                this.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            } else {
                showToast(`Maximum quantity is ${max} kg`, 'warning');
            }
        });
        
        // Handle direct input changes
        input.addEventListener('input', function() {
            let value = parseFloat(this.value);
            
            if (isNaN(value) || value < min) {
                value = min;
            } else if (value > max) {
                value = max;
                showToast(`Maximum quantity is ${max} kg`, 'warning');
            }
            
            // Round to step
            value = Math.round(value / step) * step;
            this.value = value.toFixed(1);
            updateButtonStates();
        });
        
        // Initial button state and price update
        updateButtonStates();
    });
}

/**
 * Validate quantity input
 */
function validateQuantity(input) {
    const min = parseFloat(input.getAttribute('min')) || 0.1;
    const max = parseFloat(input.getAttribute('max')) || 999;
    const step = parseFloat(input.getAttribute('step')) || 0.1;
    let value = parseFloat(input.value);
    
    if (isNaN(value) || value < min) {
        value = min;
    } else if (value > max) {
        value = max;
        showToast(`Maximum quantity is ${max} kg`, 'warning');
    }
    
    // Round to step
    value = Math.round(value / step) * step;
    input.value = value.toFixed(1);
    
    // Update total price if available
    updateItemTotal(input);
}

/**
 * Update item total price
 */
function updateItemTotal(quantityInput) {
    const container = quantityInput.closest('.card, .cart-item, .row');
    if (!container) return;
    
    const priceElement = container.querySelector('[data-price]');
    const totalElement = container.querySelector('.item-total, .total-price');
    
    if (priceElement && totalElement) {
        const price = parseFloat(priceElement.getAttribute('data-price'));
        const quantity = parseFloat(quantityInput.value);
        const total = price * quantity;
        
        totalElement.textContent = `रू ${total.toFixed(0)}`;
        
        // Update cart summary if on cart page
        updateCartSummary();
    }
}

/**
 * Update cart summary
 */
function updateCartSummary() {
    const cartItems = document.querySelectorAll('.cart-item');
    let subtotal = 0;
    
    cartItems.forEach(item => {
        const totalElement = item.querySelector('.total-price');
        if (totalElement) {
            const total = parseFloat(totalElement.textContent.replace(/[^\d.]/g, ''));
            if (!isNaN(total)) {
                subtotal += total;
            }
        }
    });
    
    // Update subtotal
    const subtotalElement = document.querySelector('.cart-subtotal');
    if (subtotalElement) {
        subtotalElement.textContent = `रू ${subtotal.toFixed(0)}`;
    }
    
    // Calculate delivery charge
    let deliveryCharge = 50;
    if (subtotal >= 2000) {
        deliveryCharge = 0;
    } else if (subtotal >= 1000) {
        deliveryCharge = 25;
    }
    
    // Update delivery charge
    const deliveryElement = document.querySelector('.delivery-charge');
    if (deliveryElement) {
        deliveryElement.textContent = deliveryCharge === 0 ? 'FREE' : `रू ${deliveryCharge}`;
    }
    
    // Update total
    const totalElement = document.querySelector('.cart-total');
    if (totalElement) {
        totalElement.textContent = `रू ${(subtotal + deliveryCharge).toFixed(0)}`;
    }
    
    // Update free delivery message
    updateFreeDeliveryMessage(subtotal);
}

/**
 * Update free delivery message
 */
function updateFreeDeliveryMessage(subtotal) {
    const messageElement = document.querySelector('.free-delivery-message');
    if (!messageElement) return;
    
    if (subtotal >= 2000) {
        messageElement.innerHTML = `
            <i class="fas fa-check-circle text-success me-2"></i>
            You qualify for FREE delivery!
        `;
        messageElement.className = 'alert alert-success p-2 mb-3';
    } else {
        const remaining = 2000 - subtotal;
        messageElement.innerHTML = `
            <i class="fas fa-truck me-2"></i>
            Add रू ${remaining.toFixed(0)} more for FREE delivery!
        `;
        messageElement.className = 'alert alert-info p-2 mb-3';
    }
}

/**
 * Update cart badge in navigation
 */
function updateCartBadge() {
    // This would typically get data from session/localStorage
    // For now, just count items on page if on cart page
    const cartItems = document.querySelectorAll('.cart-item');
    const badge = document.querySelector('.navbar .badge');
    
    if (badge && cartItems.length > 0) {
        badge.textContent = cartItems.length;
        badge.style.display = 'inline';
    }
}

/**
 * Initialize form functionality
 */
function initializeForms() {
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.dataset.noLoading) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Please wait...';
                submitBtn.disabled = true;
                
                // Restore button after timeout (fallback)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });
    
    // Real-time validation for specific fields
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', validateEmail);
    });
    
    const phoneInputs = document.querySelectorAll('input[name*="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', validatePhone);
        input.addEventListener('input', formatPhone);
    });
    
    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.name === 'password' || input.name === 'new_password') {
            input.addEventListener('input', function() {
                showPasswordStrength(this);
            });
        }
    });
    
    // Confirm password validation
    const confirmPasswordInputs = document.querySelectorAll('input[name*="confirm"], input[name*="password2"]');
    confirmPasswordInputs.forEach(input => {
        input.addEventListener('input', function() {
            validatePasswordConfirmation(this);
        });
    });
}

/**
 * Validate form before submission
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

/**
 * Validate email format
 */
function validateEmail(event) {
    const input = event.target;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (input.value && !emailRegex.test(input.value)) {
        showFieldError(input, 'Please enter a valid email address');
        return false;
    } else {
        clearFieldError(input);
        return true;
    }
}

/**
 * Validate Nepali phone number
 */
function validatePhone(event) {
    const input = event.target;
    const phoneRegex = /^(\+977[-\s]?)?9[0-9]{9}$/;
    
    if (input.value && !phoneRegex.test(input.value.replace(/[-\s]/g, ''))) {
        showFieldError(input, 'Please enter a valid Nepali mobile number (98XXXXXXXX)');
        return false;
    } else {
        clearFieldError(input);
        return true;
    }
}

/**
 * Format phone number input
 */
function formatPhone(event) {
    const input = event.target;
    let value = input.value.replace(/\D/g, '');
    
    if (value.startsWith('977')) {
        value = '+977-' + value.substring(3);
    } else if (value.length === 10 && value.startsWith('9')) {
        value = value.replace(/(\d{2})(\d{4})(\d{4})/, '$1-$2-$3');
    }
    
    input.value = value;
}

/**
 * Show password strength indicator
 */
function showPasswordStrength(input) {
    const password = input.value;
    let strength = 0;
    let feedback = [];
    
    if (password.length >= 8) strength++;
    else feedback.push('At least 8 characters');
    
    if (/[a-z]/.test(password)) strength++;
    else feedback.push('Lowercase letter');
    
    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('Uppercase letter');
    
    if (/\d/.test(password)) strength++;
    else feedback.push('Number');
    
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    else feedback.push('Special character');
    
    // Find or create strength indicator
    let strengthIndicator = input.parentNode.querySelector('.password-strength');
    if (!strengthIndicator) {
        strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength mt-2';
        input.parentNode.appendChild(strengthIndicator);
    }
    
    const strengthColors = ['danger', 'warning', 'info', 'success', 'success'];
    const strengthTexts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    
    strengthIndicator.innerHTML = `
        <div class="progress" style="height: 5px;">
            <div class="progress-bar bg-${strengthColors[strength]} progress-bar-animated" 
                 style="width: ${(strength * 20)}%"></div>
        </div>
        <small class="text-${strengthColors[strength]}">
            ${strengthTexts[strength]} ${feedback.length > 0 ? '(Missing: ' + feedback.join(', ') + ')' : ''}
        </small>
    `;
}

/**
 * Validate password confirmation
 */
function validatePasswordConfirmation(input) {
    const form = input.closest('form');
    const passwordField = form.querySelector('input[name="password"], input[name="new_password"]');
    
    if (passwordField && input.value !== passwordField.value) {
        showFieldError(input, 'Passwords do not match');
        return false;
    } else {
        clearFieldError(input);
        return true;
    }
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            // Clear any form data if needed
            const form = this.querySelector('form');
            if (form && form.dataset.clearOnClose !== 'false') {
                form.reset();
                clearFormErrors(form);
            }
        });
    });
}

/**
 * Clear form errors
 */
function clearFormErrors(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    const errorDivs = form.querySelectorAll('.invalid-feedback');
    errorDivs.forEach(div => {
        div.remove();
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe cards and other elements
    const animateElements = document.querySelectorAll('.card, .alert, .product-card');
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Counter animations for statistics
    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-counter'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        const counterObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    counterObserver.unobserve(entry.target);
                }
            });
        });
        
        counterObserver.observe(counter);
    });
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Search functionality
    const searchInput = document.querySelector('#searchInput, .search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
    
    // Filter functionality
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            applyFilters();
        });
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            
            // Validate that href is not just '#' and has a valid fragment identifier
            if (href && href.length > 1 && href !== '#') {
                try {
                    const target = document.querySelector(href);
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                } catch (error) {
                    console.warn('Invalid selector:', href, error);
                }
            }
        });
    });
    
    // Back to top button
    const backToTopBtn = createBackToTopButton();
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });
}

/**
 * Create back to top button
 */
function createBackToTopButton() {
    const btn = document.createElement('button');
    btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    btn.className = 'btn btn-primary btn-floating';
    btn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: none;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    btn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    document.body.appendChild(btn);
    return btn;
}

/**
 * Initialize page-specific functionality
 */
function initializePageSpecific() {
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('/products')) {
        initializeProductPage();
    } else if (currentPage.includes('/cart')) {
        initializeCartPage();
    } else if (currentPage.includes('/admin')) {
        initializeAdminPage();
    } else if (currentPage === '/') {
        initializeHomePage();
    }
}

/**
 * Initialize product page functionality
 */
function initializeProductPage() {
    // Product image zoom
    const productImages = document.querySelectorAll('.product-image, .card-img-top');
    productImages.forEach(img => {
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        
        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Quick view functionality
    const quickViewBtns = document.querySelectorAll('.quick-view-btn');
    quickViewBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            showQuickView(productId);
        });
    });
}

/**
 * Initialize cart page functionality
 */
function initializeCartPage() {
    // Auto-update cart totals
    updateCartSummary();
    
    // Quantity change debouncing
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            debounce(() => {
                updateCartSummary();
            }, 300)();
        });
    });
}

/**
 * Initialize admin page functionality
 */
function initializeAdminPage() {
    // Data tables enhancement
    const tables = document.querySelectorAll('.admin-table');
    tables.forEach(table => {
        enhanceTable(table);
    });
    
    // Auto-refresh for dashboard stats
    if (window.location.pathname.includes('/admin') && !window.location.pathname.includes('/admin/')) {
        setInterval(() => {
            refreshDashboardStats();
        }, 30000); // Refresh every 30 seconds
    }
}

/**
 * Initialize home page functionality
 */
function initializeHomePage() {
    // Featured products carousel
    const featuredSection = document.querySelector('.featured-products');
    if (featuredSection) {
        // Auto-scroll featured products on mobile
        if (window.innerWidth < 768) {
            const productRow = featuredSection.querySelector('.row');
            if (productRow) {
                productRow.style.overflowX = 'auto';
                productRow.style.flexWrap = 'nowrap';
            }
        }
    }
}

/**
 * Utility Functions
 */

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    bsToast.show();
    
    // Remove toast after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
    
    return bsToast;
}

/**
 * Get appropriate icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-triangle',
        info: 'info-circle',
        primary: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Show confirmation dialog
 */
function showConfirmDialog(title, message, confirmText = 'Confirm', confirmClass = 'btn-primary') {
    return new Promise((resolve) => {
        // Create modal if it doesn't exist
        let modal = document.querySelector('#confirmModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'confirmModal';
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"></h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn confirm-btn">Confirm</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Update modal content - check if elements exist
        const titleElement = modal.querySelector('.modal-title');
        const bodyElement = modal.querySelector('.modal-body');
        const confirmBtn = modal.querySelector('.confirm-btn');
        const cancelBtn = modal.querySelector('[data-bs-dismiss="modal"]');
        
        if (titleElement) titleElement.textContent = title;
        if (bodyElement) bodyElement.textContent = message;
        
        if (confirmBtn) {
            confirmBtn.textContent = confirmText;
            confirmBtn.className = `btn ${confirmClass}`;
        }
        
        // Set up event listeners
        const handleConfirm = () => {
            try {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                } else {
                    modal.style.display = 'none';
                    modal.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) backdrop.remove();
                }
            } catch (e) {
                console.warn('Error hiding modal:', e);
            }
            resolve(true);
        };
        
        const handleCancel = () => {
            try {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                } else {
                    modal.style.display = 'none';
                    modal.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) backdrop.remove();
                }
            } catch (e) {
                console.warn('Error hiding modal:', e);
            }
            resolve(false);
        };
        
        // Remove existing listeners and add new ones
        if (confirmBtn) {
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            newConfirmBtn.addEventListener('click', handleConfirm);
        }
        
        if (cancelBtn) {
            const newCancelBtn = cancelBtn.cloneNode(true);
            cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
            newCancelBtn.addEventListener('click', handleCancel);
        }
        
        // Show modal
        try {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
                
                modal.addEventListener('hidden.bs.modal', () => {
                    resolve(false);
                }, { once: true });
            } else {
                // Fallback if Bootstrap is not available
                modal.style.display = 'block';
                modal.classList.add('show');
                document.body.classList.add('modal-open');
            }
        } catch (e) {
            console.error('Error showing modal:', e);
            // Simple fallback confirmation
            const confirmed = confirm(`${title}\n\n${message}`);
            resolve(confirmed);
        }
    });
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
 * Format currency (Nepali Rupees)
 */
function formatCurrency(amount) {
    return `रू ${parseFloat(amount).toLocaleString('en-IN')}`;
}

/**
 * Validate file upload
 */
function validateFileUpload(file, allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'], maxSize = 5 * 1024 * 1024) {
    if (!allowedTypes.includes(file.type)) {
        showToast('Please select a valid image file (JPG, PNG, GIF)', 'danger');
        return false;
    }
    
    if (file.size > maxSize) {
        showToast('File size must be less than 5MB', 'danger');
        return false;
    }
    
    return true;
}

/**
 * Handle AJAX requests with proper error handling
 */
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showToast('An error occurred. Please try again.', 'danger');
            throw error;
        });
}

/**
 * Local storage helpers
 */
const LocalStorage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn('LocalStorage not available:', e);
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn('LocalStorage not available:', e);
        }
    }
};

/**
 * Increase quantity for cart items
 */
function increaseQuantity(index) {
    const quantityInput = document.querySelector(`#quantity_${index}`);
    if (quantityInput) {
        const currentValue = parseFloat(quantityInput.value) || 0;
        const step = parseFloat(quantityInput.getAttribute('step')) || 0.1;
        const max = parseFloat(quantityInput.getAttribute('max')) || 999;
        
        const newValue = currentValue + step;
        if (newValue <= max) {
            quantityInput.value = newValue.toFixed(1);
            validateQuantity(quantityInput);
            
            // Auto-submit the form after a short delay
            setTimeout(() => {
                quantityInput.closest('form').submit();
            }, 300);
        } else {
            showToast(`Maximum quantity is ${max} kg`, 'warning');
        }
    }
}

/**
 * Decrease quantity for cart items
 */
function decreaseQuantity(index) {
    const quantityInput = document.querySelector(`#quantity_${index}`);
    if (quantityInput) {
        const currentValue = parseFloat(quantityInput.value) || 0;
        const step = parseFloat(quantityInput.getAttribute('step')) || 0.1;
        const min = parseFloat(quantityInput.getAttribute('min')) || 0.1;
        
        const newValue = currentValue - step;
        if (newValue >= min) {
            quantityInput.value = newValue.toFixed(1);
            validateQuantity(quantityInput);
            
            // Auto-submit the form after a short delay
            setTimeout(() => {
                quantityInput.closest('form').submit();
            }, 300);
        } else {
            showToast(`Minimum quantity is ${min} kg`, 'warning');
        }
    }
}

/**
 * Initialize cart button event listeners
 */
function initializeCartButtons() {
    // Add event listeners for increase buttons
    document.querySelectorAll('.increase-btn').forEach(button => {
        button.addEventListener('click', function() {
            const index = this.getAttribute('data-index');
            increaseQuantity(index);
        });
    });
    
    // Add event listeners for decrease buttons
    document.querySelectorAll('.decrease-btn').forEach(button => {
        button.addEventListener('click', function() {
            const index = this.getAttribute('data-index');
            decreaseQuantity(index);
        });
    });
    
    // Add event listeners for quantity input changes
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            validateQuantity(this);
            setTimeout(() => {
                this.closest('form').submit();
            }, 300);
        });
    });
}

// Export functions for global access
window.MeatShop = {
    showToast,
    showConfirmDialog,
    formatCurrency,
    validateFileUpload,
    makeRequest,
    LocalStorage,
    updateCartSummary,
    validateQuantity,
    increaseQuantity,
    decreaseQuantity
};

// Make functions globally available
window.increaseQuantity = increaseQuantity;
window.decreaseQuantity = decreaseQuantity;

// Service Worker registration removed to prevent 404 errors
// If you want PWA capabilities, create a sw.js file in the static folder

console.log('🍖 Nepal Meat Shop JavaScript loaded successfully!');
