#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Configuration Settings
Centralized configuration for the Flask application.
"""

import os

class Config:
    """Base configuration class with common settings."""
    
    # Security Configuration
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    
    # MongoDB Configuration (SQLAlchemy removed)
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Application Configuration
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    @staticmethod
    def init_app(app):
        """Initialize application-specific configuration."""
        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    # MongoDB Atlas configuration from environment
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop'

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop'
    
class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/nepal_meat_shop_test'
    MONGO_DBNAME = 'nepal_meat_shop_test'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}