#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Configuration Settings
MongoDB-specific configuration for the Flask application.
"""

import os
from datetime import timedelta

class MongoConfig:
    """
    Base MongoDB configuration class.
    """
    # MongoDB settings - supports both local and Atlas
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/nepal_meat_shop'
    MONGO_HOST = os.environ.get('MONGO_HOST') or 'localhost'
    MONGO_PORT = int(os.environ.get('MONGO_PORT') or 27017)
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop'
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'nepal_meat_shop'
    
    # MongoDB Atlas settings (if using cloud)
    MONGO_ATLAS_URI = os.environ.get('MONGO_ATLAS_URI')
    MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nepal-meat-shop-secret-key-2024'
    WTF_CSRF_ENABLED = True
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

class MongoDevelopmentConfig(MongoConfig):
    """Development environment configuration for MongoDB."""
    DEBUG = True
    # Use environment variable if set, otherwise default to local dev database
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/nepal_meat_shop_dev'
    MONGO_DBNAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop_dev'

class MongoProductionConfig(MongoConfig):
    """Production environment configuration for MongoDB."""
    DEBUG = False
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/nepal_meat_shop'
    
class MongoTestingConfig(MongoConfig):
    """Testing environment configuration for MongoDB."""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/nepal_meat_shop_test'
    MONGO_DBNAME = 'nepal_meat_shop_test'
    WTF_CSRF_ENABLED = False

# Configuration mapping for MongoDB
mongo_config = {
    'development': MongoDevelopmentConfig,
    'production': MongoProductionConfig,
    'testing': MongoTestingConfig,
    'default': MongoDevelopmentConfig
}