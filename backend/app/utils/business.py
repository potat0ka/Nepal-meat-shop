#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Business Utilities
Business logic utilities for orders, pricing, and inventory.
"""

import uuid
from datetime import datetime

def generate_order_number():
    """
    Generate a unique order number for meat shop orders.
    
    Returns:
        str: Unique order number in format MO + timestamp + random
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"MO{timestamp}{random_suffix}"

def generate_invoice_number():
    """
    Generate a unique invoice number for billing.
    
    Returns:
        str: Unique invoice number in format INV + timestamp + random
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"INV{timestamp}{random_suffix}"

def format_currency(amount):
    """
    Format amount as Nepali currency with proper formatting.
    
    Args:
        amount: The amount to format (float or int)
    
    Returns:
        str: Formatted currency string (e.g., "NPR 1,250.00")
    """
    if amount is None:
        return "NPR 0.00"
    
    return f"NPR {amount:,.2f}"

def calculate_delivery_charge(subtotal, delivery_area=None):
    """
    Calculate delivery charge based on order amount and delivery area.
    
    Args:
        subtotal: Order subtotal amount
        delivery_area: Optional delivery area object with delivery_charge attribute
    
    Returns:
        float: Delivery charge amount
    """
    # Free delivery for orders above NPR 2000
    if subtotal >= 2000:
        return 0.0
    
    # Reduced delivery for orders above NPR 1000
    if subtotal >= 1000:
        return 25.0
    
    # Use area-specific delivery charge if available
    if delivery_area and hasattr(delivery_area, 'delivery_charge'):
        return float(delivery_area.delivery_charge)
    
    # Default delivery charge
    return 50.0

def get_stock_status(product):
    """
    Get stock status information for a product.
    
    Args:
        product: Product object with stock_kg attribute
    
    Returns:
        dict: Status info with 'label' and 'class' keys for UI display
    """
    stock_kg = getattr(product, 'stock_kg', 0)
    
    if stock_kg <= 0:
        return {'label': 'Out of Stock', 'class': 'danger'}
    elif stock_kg <= 5:
        return {'label': 'Low Stock', 'class': 'warning'}
    elif stock_kg <= 20:
        return {'label': 'Limited Stock', 'class': 'info'}
    else:
        return {'label': 'In Stock', 'class': 'success'}

def get_meat_type_display(meat_type):
    """
    Get display name for meat type in both English and Nepali.
    
    Args:
        meat_type: Meat type code (string)
    
    Returns:
        str: Display name with both Nepali and English
    """
    meat_types = {
        'pork': 'सुंगुर / Pork',
        'buffalo': 'भैंसी / Buffalo', 
        'chicken': 'कुखुरा / Chicken',
        'goat': 'खसी / Goat',
        'mutton': 'मटन / Mutton',
        'fish': 'माछा / Fish'
    }
    return meat_types.get(meat_type.lower() if meat_type else '', meat_type)

def get_order_status_badge_class(status):
    """
    Get Bootstrap badge class for order status display.
    
    Args:
        status: Order status string
    
    Returns:
        str: Bootstrap badge class name
    """
    status_classes = {
        'pending': 'bg-warning',
        'confirmed': 'bg-info',
        'processing': 'bg-primary',
        'out_for_delivery': 'bg-secondary',
        'delivered': 'bg-success',
        'cod_paid': 'bg-success',
        'cancelled': 'bg-danger',
        'refunded': 'bg-dark'
    }
    return status_classes.get(status.lower() if status else '', 'bg-secondary')

def calculate_order_total(items, delivery_charge=0):
    """
    Calculate total order amount including delivery.
    
    Args:
        items: List of order items with price and quantity
        delivery_charge: Delivery charge amount
    
    Returns:
        dict: Dictionary with subtotal, delivery_charge, and total
    """
    subtotal = sum(item.price * item.quantity for item in items)
    total = subtotal + delivery_charge
    
    return {
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'total': total
    }