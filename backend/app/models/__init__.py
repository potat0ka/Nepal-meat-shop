"""
🍖 Nepal Meat Shop - Models Package
Centralized import for all database models.
"""

# Import MongoDB models
from .mongo_models import MongoUser, MongoProduct, MongoOrder, MongoCategory

# Export all models for easy importing
__all__ = [
    'MongoUser',
    'MongoProduct', 
    'MongoOrder', 
    'MongoCategory'
]