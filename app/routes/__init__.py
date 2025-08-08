#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Routes Package
Centralized route registration and blueprint management.
"""

from .main import main_bp
from .auth import auth_bp
from .products import products_bp
from .orders import orders_bp

def register_blueprints(app):
    """
    Register all application blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Register main routes (home, about, etc.)
    app.register_blueprint(main_bp)
    
    # Register authentication routes
    app.register_blueprint(auth_bp)
    
    # Register product routes
    app.register_blueprint(products_bp)
    
    # Register order and cart routes
    app.register_blueprint(orders_bp)

# Make blueprints available for direct import
__all__ = [
    'main_bp',
    'auth_bp', 
    'products_bp',
    'orders_bp',
    'register_blueprints'
]