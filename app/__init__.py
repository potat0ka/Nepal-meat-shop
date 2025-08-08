#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Application Factory
Main Flask application setup with modular architecture.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

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
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'कृपया पहिले लगइन गर्नुहोस् / Please log in first'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            # Handle invalid user_id format (e.g., from old sessions)
            return None
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.orders import orders_bp
    from app.routes.mongo_admin import mongo_admin_bp
    from app.routes.mongo_orders import mongo_orders_bp
    from app.routes.payment_webhooks import payment_webhooks_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(mongo_admin_bp, url_prefix='/admin')
    app.register_blueprint(mongo_orders_bp, url_prefix='/orders')
    app.register_blueprint(payment_webhooks_bp)
    
    # Register template filters and context processors
    register_template_helpers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
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