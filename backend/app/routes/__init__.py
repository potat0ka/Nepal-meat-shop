#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Routes Package
Centralized route registration and blueprint management.
"""

from .mongo_main import mongo_main_bp
from .mongo_auth import mongo_auth_bp
from .mongo_products import mongo_products_bp
from .mongo_orders import mongo_orders_bp
from .mongo_admin import mongo_admin_bp

def register_blueprints(app):
    """
    Register all application blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Register main routes (home, about, etc.)
    app.register_blueprint(mongo_main_bp)
    
    # Register authentication routes
    app.register_blueprint(mongo_auth_bp)
    
    # Register product routes
    app.register_blueprint(mongo_products_bp)
    
    # Register order and cart routes
    app.register_blueprint(mongo_orders_bp)
    
    # Register admin routes
    app.register_blueprint(mongo_admin_bp)

# Make blueprints available for direct import
__all__ = [
    'mongo_main_bp',
    'mongo_auth_bp', 
    'mongo_products_bp',
    'mongo_orders_bp',
    'mongo_admin_bp',
    'register_blueprints'
]