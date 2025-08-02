import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file, folder):
    """
    Save uploaded file to the specified folder.
    
    Args:
        file: The uploaded file object
        folder: The subfolder name (e.g., 'products', 'reviews')
    
    Returns:
        str: The relative path to the saved file
    """
    if file and file.filename:
        # Get secure filename
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid filename conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create folder path
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(folder_path, unique_filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"{folder}/{unique_filename}"
    
    return None

def generate_order_number():
    """
    Generate a unique order number.
    
    Returns:
        str: Unique order number in format MO + timestamp + random
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"MO{timestamp}{random_suffix}"

def format_currency(amount):
    """
    Format amount as Nepali currency.
    
    Args:
        amount: The amount to format
    
    Returns:
        str: Formatted currency string
    """
    return f"NPR {amount:,.2f}"

def calculate_delivery_charge(subtotal, delivery_area=None):
    """
    Calculate delivery charge based on order amount and area.
    
    Args:
        subtotal: Order subtotal amount
        delivery_area: Optional delivery area object
    
    Returns:
        float: Delivery charge amount
    """
    # Free delivery for orders above NPR 2000
    if subtotal >= 2000:
        return 0.0
    
    # Reduced delivery for orders above NPR 1000
    if subtotal >= 1000:
        return 25.0
    
    # Default delivery charge
    if delivery_area and hasattr(delivery_area, 'delivery_charge'):
        return delivery_area.delivery_charge
    
    return 50.0

def get_stock_status(product):
    """
    Get stock status label for a product.
    
    Args:
        product: Product object
    
    Returns:
        dict: Status info with label and class
    """
    if product.stock_kg <= 0:
        return {'label': 'Out of Stock', 'class': 'danger'}
    elif product.stock_kg <= 5:
        return {'label': 'Low Stock', 'class': 'warning'}
    elif product.stock_kg <= 20:
        return {'label': 'Limited Stock', 'class': 'info'}
    else:
        return {'label': 'In Stock', 'class': 'success'}

def generate_invoice_number():
    """
    Generate a unique invoice number.
    
    Returns:
        str: Unique invoice number in format INV + timestamp + random
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"INV{timestamp}{random_suffix}"

def validate_phone_number(phone):
    """
    Validate Nepali phone number format.
    
    Args:
        phone: Phone number string
    
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    # Nepali mobile number pattern (98xxxxxxxx or +977-98xxxxxxxx)
    pattern = r'^(\+977[-\s]?)?9[0-9]{9}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

def truncate_text(text, length=100):
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        length: Maximum length
    
    Returns:
        str: Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    return text[:length].rsplit(' ', 1)[0] + '...'

def get_meat_type_display(meat_type):
    """
    Get display name for meat type in both English and Nepali.
    
    Args:
        meat_type: Meat type code
    
    Returns:
        str: Display name
    """
    meat_types = {
        'pork': 'सुंगुर / Pork',
        'buffalo': 'भैंसी / Buffalo',
        'chicken': 'कुखुरा / Chicken',
        'goat': 'खसी / Goat'
    }
    return meat_types.get(meat_type, meat_type)

def get_order_status_badge_class(status):
    """
    Get Bootstrap badge class for order status.
    
    Args:
        status: Order status
    
    Returns:
        str: Bootstrap badge class
    """
    status_classes = {
        'pending': 'bg-warning',
        'confirmed': 'bg-info',
        'processing': 'bg-primary',
        'out_for_delivery': 'bg-secondary',
        'delivered': 'bg-success',
        'cancelled': 'bg-danger'
    }
    return status_classes.get(status, 'bg-secondary')
