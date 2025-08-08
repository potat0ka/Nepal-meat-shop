"""
🍖 Nepal Meat Shop - Models Package
Centralized import for all database models.
"""

# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .product import Category, Product, Review, StockAlert
from .order import Order, OrderItem, CartItem, DeliveryArea, Invoice
from .analytics import SalesReport, NotificationTemplate, NotificationLog

# Export all models for easy importing
__all__ = [
    'User',
    'Category', 'Product', 'Review', 'StockAlert',
    'Order', 'OrderItem', 'CartItem', 'DeliveryArea', 'Invoice',
    'SalesReport', 'NotificationTemplate', 'NotificationLog'
]