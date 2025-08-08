#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - User Models
User authentication and profile management models.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

class User(UserMixin, db.Model):
    """
    User model for customer and admin accounts.
    Handles authentication, profile data, and user relationships.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash for secure storage."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_cart_total(self):
        """Calculate total value of items in user's cart."""
        total = 0
        for item in self.cart_items:
            total += item.quantity * item.product.price
        return total
    
    def get_cart_count(self):
        """Get total number of items in user's cart."""
        return sum(item.quantity for item in self.cart_items)
    
    def __repr__(self):
        return f'<User {self.username}>'