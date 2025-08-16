#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Application Factory
Main Flask application setup with modular architecture.
"""

import os
import logging
from flask import Flask
from flask_login import LoginManager

# Initialize extensions (SQLAlchemy removed - using MongoDB only)
login_manager = LoginManager()

def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask app with correct template and static folder paths
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/meatshop.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Nepal Meat Shop startup')
    
    # Initialize MongoDB connection
    from app.utils.mongo_db import mongo_db
    mongo_db.init_app(app)
    
    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'कृपया पहिले लगइन गर्नुहोस् / Please log in first'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.utils.mongo_db import mongo_db
        try:
            return mongo_db.find_user_by_id(user_id)
        except (ValueError, TypeError):
            # Handle invalid user_id format (e.g., from old sessions)
            return None
    
    # Register blueprints - Using MongoDB routes only
    from app.routes.main import main_bp
    from app.routes.mongo_auth import mongo_auth_bp
    from app.routes.mongo_admin import mongo_admin_bp
    from app.routes.mongo_orders import mongo_orders_bp
    from app.routes.mongo_products import mongo_products_bp
    from app.routes.mongo_main import mongo_main_bp
    from app.routes.payment_webhooks import payment_webhooks_bp
    from app.routes.chat import chat_bp
    from app.routes.admin_chat import admin_chat_bp
    
    # Register MongoDB-based blueprints
    app.register_blueprint(mongo_main_bp)  # MongoDB main routes
    app.register_blueprint(main_bp)  # Keep for compatibility
    app.register_blueprint(mongo_auth_bp, url_prefix='/auth')
    app.register_blueprint(mongo_admin_bp, url_prefix='/admin')
    app.register_blueprint(mongo_orders_bp, url_prefix='/orders')
    app.register_blueprint(mongo_products_bp, url_prefix='/products')
    app.register_blueprint(payment_webhooks_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_chat_bp)
    
    # Register template filters and context processors
    register_template_helpers(app)
    
    # MongoDB connection is handled by mongo_db.init_app()
    
    return app

def register_template_helpers(app):
    """
    Register template filters and context processors.
    """
    from app.utils import format_currency, get_stock_status, truncate_text
    
    # Template filters
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['truncate_text'] = truncate_text
    
    # Context processors
    @app.context_processor
    def inject_template_globals():
        return {
            'format_currency': format_currency,
            'get_stock_status': get_stock_status
        }