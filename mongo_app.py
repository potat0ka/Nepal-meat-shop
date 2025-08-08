#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Flask Application
Main Flask application setup with MongoDB integration.
"""

import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env.mongo
load_dotenv('.env.mongo')

from app.config.mongo_settings import mongo_config
from app.utils.mongo_db import mongo_db

def create_mongo_app(config_name=None):
    """
    Application factory for MongoDB version.
    Creates and configures the Flask application with MongoDB.
    """
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(mongo_config[config_name])
    
    # Initialize MongoDB
    mongo_db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'कृपया लगइन गर्नुहोस् / Please login to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        return mongo_db.find_user_by_id(user_id)
    
    # Register blueprints
    from app.routes.mongo_auth import mongo_auth_bp
    from app.routes.mongo_main import mongo_main_bp
    from app.routes.mongo_products import mongo_products_bp
    from app.routes.mongo_orders import mongo_orders_bp
    from app.routes.mongo_admin import mongo_admin_bp
    from app.routes.payment_api import payment_api
    from app.routes.payment_callbacks import payment_callbacks
    
    app.register_blueprint(mongo_main_bp)
    app.register_blueprint(mongo_auth_bp)
    app.register_blueprint(mongo_products_bp)
    app.register_blueprint(mongo_orders_bp)
    app.register_blueprint(mongo_admin_bp)
    app.register_blueprint(payment_api)
    app.register_blueprint(payment_callbacks)
    
    # Create upload directories
    upload_dirs = ['uploads', 'uploads/products', 'uploads/profiles']
    for upload_dir in upload_dirs:
        os.makedirs(upload_dir, exist_ok=True)
    
    # Configure logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.info('🍖 Nepal Meat Shop (MongoDB) startup')
    
    # Application startup message
    print("\n" + "="*50)
    print("🍖 Starting Nepal Meat Shop (MongoDB Version)")
    print(f"📍 Running on: http://127.0.0.1:5000")
    print(f"🔧 Environment: {config_name}")
    print(f"🐛 Debug mode: {app.debug}")
    print(f"🗄️  Database: MongoDB ({app.config.get('MONGO_DBNAME', 'nepal_meat_shop')})")
    print("="*50)
    
    return app

if __name__ == '__main__':
    app = create_mongo_app()
    app.run(debug=True, host='127.0.0.1', port=5000)