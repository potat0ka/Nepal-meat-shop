#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Product Models
Product catalog, categories, and inventory management models.
"""

from datetime import datetime
# SQLAlchemy removed - using MongoDB models instead

class Category(db.Model):
    """
    Product categories for organizing meat cuts.
    Supports bilingual names (English/Nepali).
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_nepali = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    """
    Product model for meat items with comprehensive details.
    Includes pricing, stock management, and freshness tracking.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    name_nepali = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price per kg
    image_url = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    meat_type = db.Column(db.String(50), nullable=False)  # 'pork' or 'buffalo'
    preparation_type = db.Column(db.String(50), default='fresh')  # fresh, processed, etc.
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    stock_kg = db.Column(db.Float, default=0)  # Stock in kilograms
    min_order_kg = db.Column(db.Float, default=0.5)  # Minimum order quantity
    freshness_hours = db.Column(db.Integer, default=24)  # Hours since processing
    cooking_tips = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    
    def get_average_rating(self):
        """Calculate average rating from customer reviews."""
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    def get_freshness_label(self):
        """Get freshness label based on processing hours."""
        if self.freshness_hours <= 6:
            return "आज ताजा / Fresh Today"
        elif self.freshness_hours <= 24:
            return "हिजो काटिएको / Cut Yesterday"
        else:
            return "स्टक / Stock"
    
    def is_in_stock(self, quantity_kg):
        """Check if requested quantity is available in stock."""
        return self.stock_kg >= quantity_kg
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Review(db.Model):
    """
    Product reviews and ratings from customers.
    Supports image uploads and approval workflow.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.rating} stars for Product {self.product_id}>'

class StockAlert(db.Model):
    """
    Stock alert system for low inventory management.
    Automatically tracks when products need restocking.
    """
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    threshold_kg = db.Column(db.Float, nullable=False, default=5.0)
    is_active = db.Column(db.Boolean, default=True)
    last_alert_sent = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    product = db.relationship('Product', backref='stock_alerts')
    
    def needs_alert(self):
        """Check if product stock is below threshold and needs alert."""
        return self.product.stock_kg <= self.threshold_kg
    
    def __repr__(self):
        return f'<StockAlert for Product {self.product_id}>'