#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Database Utilities
MongoDB connection and database operation utilities.
"""

from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import current_app
from app.models.mongo_models import MongoUser, MongoProduct, MongoOrder, MongoCategory

class MongoDB:
    """MongoDB database connection and operations."""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    def init_app(self, app):
        """Initialize MongoDB with Flask app."""
        self.client = MongoClient(app.config['MONGO_URI'])
        self.db = self.client[app.config['MONGO_DBNAME']]
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance."""
        # User indexes
        self.db.users.create_index('email', unique=True)
        self.db.users.create_index('username', unique=True)
        self.db.users.create_index('phone', unique=True)  # Add phone index
        
        # Product indexes
        self.db.products.create_index('name')
        self.db.products.create_index('category')
        self.db.products.create_index('meat_type')
        self.db.products.create_index('is_available')
        self.db.products.create_index('is_featured')
        
        # Order indexes
        self.db.orders.create_index('user_id')
        self.db.orders.create_index('status')
        self.db.orders.create_index('order_date')
        
        # Category indexes
        self.db.categories.create_index('name', unique=True)
        self.db.categories.create_index('sort_order')
    
    # User operations
    def find_user_by_id(self, user_id):
        """Find user by ID."""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            user_data = self.db.users.find_one({'_id': user_id})
            return MongoUser(user_data) if user_data else None
        except:
            return None
    
    def find_user_by_email(self, email):
        """Find user by email."""
        user_data = self.db.users.find_one({'email': email})
        return MongoUser(user_data) if user_data else None
    
    def find_user_by_username(self, username):
        """Find user by username."""
        user_data = self.db.users.find_one({'username': username})
        return MongoUser(user_data) if user_data else None
    
    def find_user_by_phone(self, phone):
        """Find user by phone number."""
        user_data = self.db.users.find_one({'phone': phone})
        return MongoUser(user_data) if user_data else None
    
    def find_user_by_reset_token(self, reset_token):
        """Find user by reset token."""
        user_data = self.db.users.find_one({'reset_token': reset_token})
        return MongoUser(user_data) if user_data else None
    
    def save_user(self, user):
        """Save or update user."""
        user_dict = user.to_dict()
        if user._id:
            # Update existing user
            self.db.users.update_one(
                {'_id': user._id},
                {'$set': user_dict}
            )
        else:
            # Create new user
            result = self.db.users.insert_one(user_dict)
            user._id = result.inserted_id
        return user
    
    def get_all_users(self):
        """Get all users."""
        users_data = self.db.users.find()
        return [MongoUser(user_data) for user_data in users_data]
    
    # Product operations
    def find_product_by_id(self, product_id):
        """Find product by ID."""
        try:
            if isinstance(product_id, str):
                product_id = ObjectId(product_id)
            product_data = self.db.products.find_one({'_id': product_id})
            return MongoProduct(product_data) if product_data else None
        except:
            return None
    
    def get_all_products(self, category=None, meat_type=None, available_only=True):
        """Get all products with optional filtering."""
        query = {}
        if category:
            query['category'] = category
        if meat_type:
            query['meat_type'] = meat_type
        if available_only:
            query['is_available'] = True
        
        products_data = self.db.products.find(query).sort('name', 1)
        return [MongoProduct(product_data) for product_data in products_data]
    
    def get_featured_products(self):
        """Get featured products."""
        products_data = self.db.products.find({
            'is_featured': True,
            'is_available': True
        }).sort('name', 1)
        return [MongoProduct(product_data) for product_data in products_data]
    
    def save_product(self, product):
        """Save or update product."""
        product_dict = product.to_dict()
        if product._id:
            # Update existing product
            self.db.products.update_one(
                {'_id': product._id},
                {'$set': product_dict}
            )
        else:
            # Create new product
            result = self.db.products.insert_one(product_dict)
            product._id = result.inserted_id
        return product
    
    # Order operations
    def find_order_by_id(self, order_id):
        """Find order by ID."""
        try:
            if isinstance(order_id, str):
                order_id = ObjectId(order_id)
            order_data = self.db.orders.find_one({'_id': order_id})
            return MongoOrder(order_data) if order_data else None
        except:
            return None
    
    def get_user_orders(self, user_id):
        """Get all orders for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        orders_data = self.db.orders.find({'user_id': user_id}).sort('order_date', -1)
        return [MongoOrder(order_data) for order_data in orders_data]
    
    def get_all_orders(self, status=None):
        """Get all orders with optional status filtering."""
        query = {}
        if status:
            query['status'] = status
        
        orders_data = self.db.orders.find(query).sort('order_date', -1)
        return [MongoOrder(order_data) for order_data in orders_data]
    
    def save_order(self, order):
        """Save or update order."""
        order_dict = order.to_dict()
        if order._id:
            # Update existing order
            self.db.orders.update_one(
                {'_id': order._id},
                {'$set': order_dict}
            )
        else:
            # Create new order
            result = self.db.orders.insert_one(order_dict)
            order._id = result.inserted_id
        return order
    
    # Category operations
    def get_all_categories(self):
        """Get all categories."""
        categories_data = self.db.categories.find({'is_active': True}).sort('sort_order', 1)
        return [MongoCategory(category_data) for category_data in categories_data]
    
    def find_category_by_name(self, name):
        """Find category by name."""
        category_data = self.db.categories.find_one({'name': name})
        return MongoCategory(category_data) if category_data else None
    
    def find_category_by_id(self, category_id):
        """Find category by ID."""
        try:
            if isinstance(category_id, str):
                category_id = ObjectId(category_id)
            category_data = self.db.categories.find_one({'_id': category_id})
            return MongoCategory(category_data) if category_data else None
        except:
            return None
    
    def save_category(self, category):
        """Save or update category."""
        category_dict = category.to_dict()
        if category._id:
            # Update existing category
            self.db.categories.update_one(
                {'_id': category._id},
                {'$set': category_dict}
            )
        else:
            # Create new category
            result = self.db.categories.insert_one(category_dict)
            category._id = result.inserted_id
        return category

# Global MongoDB instance
mongo_db = MongoDB()