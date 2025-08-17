#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Validation Utilities
Input validation and data sanitization utilities.
"""

import re
from datetime import datetime

def validate_phone_number(phone):
    """
    Validate Nepali phone number format.
    
    Args:
        phone: Phone number string
    
    Returns:
        bool: True if valid Nepali phone number, False otherwise
    """
    if not phone:
        return False
    
    # Clean phone number (remove spaces, dashes, parentheses)
    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Nepali mobile number patterns:
    # - 98xxxxxxxx (10 digits starting with 98)
    # - +977-98xxxxxxxx or +97798xxxxxxxx
    # - 977-98xxxxxxxx or 97798xxxxxxxx
    patterns = [
        r'^9[0-9]{9}$',  # 98xxxxxxxx format
        r'^\+977[0-9]{10}$',  # +977xxxxxxxxxx format
        r'^977[0-9]{10}$'  # 977xxxxxxxxxx format
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)

def validate_email(email):
    """
    Validate email address format.
    
    Args:
        email: Email address string
    
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password):
    """
    Validate password strength requirements.
    
    Args:
        password: Password string
    
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if not password:
        errors.append("Password is required")
        return {'valid': False, 'errors': errors}
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    return {'valid': len(errors) == 0, 'errors': errors}

def sanitize_text(text, max_length=None):
    """
    Sanitize text input by removing dangerous characters.
    
    Args:
        text: Input text string
        max_length: Optional maximum length to truncate
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove HTML tags and dangerous characters
    sanitized = re.sub(r'<[^>]*>', '', str(text))
    sanitized = sanitized.strip()
    
    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + '...'
    
    return sanitized

def truncate_text(text, length=100):
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        length: Maximum length (default: 100)
    
    Returns:
        str: Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    # Try to break at word boundary
    truncated = text[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > length * 0.8:  # If space is reasonably close to end
        return text[:last_space] + '...'
    else:
        return text[:length] + '...'

def validate_quantity(quantity, min_qty=1, max_qty=100):
    """
    Validate quantity input for orders.
    
    Args:
        quantity: Quantity value (string or number)
        min_qty: Minimum allowed quantity
        max_qty: Maximum allowed quantity
    
    Returns:
        dict: Validation result with 'valid' boolean, 'value' and 'error'
    """
    try:
        qty = float(quantity)
        
        if qty < min_qty:
            return {'valid': False, 'value': None, 'error': f'Minimum quantity is {min_qty}'}
        
        if qty > max_qty:
            return {'valid': False, 'value': None, 'error': f'Maximum quantity is {max_qty}'}
        
        return {'valid': True, 'value': qty, 'error': None}
    
    except (ValueError, TypeError):
        return {'valid': False, 'value': None, 'error': 'Invalid quantity format'}

def validate_price(price):
    """
    Validate price input.
    
    Args:
        price: Price value (string or number)
    
    Returns:
        dict: Validation result with 'valid' boolean, 'value' and 'error'
    """
    try:
        price_val = float(price)
        
        if price_val < 0:
            return {'valid': False, 'value': None, 'error': 'Price cannot be negative'}
        
        if price_val > 100000:  # Max price NPR 100,000
            return {'valid': False, 'value': None, 'error': 'Price too high'}
        
        return {'valid': True, 'value': round(price_val, 2), 'error': None}
    
    except (ValueError, TypeError):
        return {'valid': False, 'value': None, 'error': 'Invalid price format'}