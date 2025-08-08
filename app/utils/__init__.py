#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Utilities Package
Centralized utilities for file handling, business logic, and validation.
"""

# File utilities
from .file_utils import (
    save_uploaded_file,
    delete_file,
    get_file_url,
    validate_image_file
)

# Business utilities
from .business import (
    generate_order_number,
    generate_invoice_number,
    format_currency,
    calculate_delivery_charge,
    get_stock_status,
    get_meat_type_display,
    get_order_status_badge_class,
    calculate_order_total
)

# Validation utilities
from .validation import (
    validate_phone_number,
    validate_email,
    validate_password_strength,
    sanitize_text,
    truncate_text,
    validate_quantity,
    validate_price
)

# Make all utilities available when importing from app.utils
__all__ = [
    # File utilities
    'save_uploaded_file',
    'delete_file', 
    'get_file_url',
    'validate_image_file',
    
    # Business utilities
    'generate_order_number',
    'generate_invoice_number',
    'format_currency',
    'calculate_delivery_charge',
    'get_stock_status',
    'get_meat_type_display',
    'get_order_status_badge_class',
    'calculate_order_total',
    
    # Validation utilities
    'validate_phone_number',
    'validate_email',
    'validate_password_strength',
    'sanitize_text',
    'truncate_text',
    'validate_quantity',
    'validate_price'
]