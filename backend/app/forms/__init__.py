"""
🍖 Nepal Meat Shop - Forms Package
Centralized import for all WTForms.
"""

# Import all forms for easy access
from .auth import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from .product import ProductForm, CategoryForm, ReviewForm, ProductFilterForm
from .order import CartForm, UpdateCartForm, RemoveCartForm, CheckoutForm, OrderStatusForm, OrderFilterForm

# Export all forms
__all__ = [
    # Authentication forms
    'LoginForm', 'RegisterForm', 'ProfileForm', 'ChangePasswordForm', 'ForgotPasswordForm', 'ResetPasswordForm',
    # Product forms
    'ProductForm', 'CategoryForm', 'ReviewForm', 'ProductFilterForm',
    # Order and cart forms
    'CartForm', 'UpdateCartForm', 'RemoveCartForm', 'CheckoutForm', 'OrderStatusForm', 'OrderFilterForm'
]