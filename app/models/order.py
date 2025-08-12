#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Order Models
Order management, cart functionality, and delivery models.
"""

from datetime import datetime
# SQLAlchemy removed - using MongoDB models instead

class Order(db.Model):
    """
    Order model for customer purchases.
    Handles order lifecycle from creation to delivery.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, processing, delivered, cancelled
    payment_method = db.Column(db.String(50), nullable=False)  # cod, esewa, khalti, etc.
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    transaction_id = db.Column(db.String(100))  # Payment gateway transaction ID
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_phone = db.Column(db.String(20), nullable=False)
    delivery_date = db.Column(db.DateTime)
    special_instructions = db.Column(db.Text)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def generate_order_number(self):
        """Generate unique order number with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.order_number = f"MO{timestamp}"
    
    def get_status_nepali(self):
        """Get order status in Nepali language."""
        status_map = {
            'pending': 'पेन्डिङ / Pending',
            'confirmed': 'पुष्टि भयो / Confirmed',
            'processing': 'तयारी हुँदैछ / Processing',
            'out_for_delivery': 'डेलिभरीमा / Out for Delivery',
            'delivered': 'डेलिभर भयो / Delivered',
            'cancelled': 'रद्द भयो / Cancelled'
        }
        return status_map.get(self.status, self.status)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    """
    Individual items within an order.
    Stores product details at time of purchase.
    """
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.quantity_kg}kg of Product {self.product_id}>'

class CartItem(db.Model):
    """
    Shopping cart items for temporary storage before checkout.
    Allows customers to build their order gradually.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Quantity in kg
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_total_price(self):
        """Calculate total price for this cart item."""
        return self.quantity * self.product.price
    
    def __repr__(self):
        return f'<CartItem {self.quantity}kg of Product {self.product_id}>'

class DeliveryArea(db.Model):
    """
    Delivery areas and associated charges.
    Manages delivery zones within Kathmandu Valley.
    """
    id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(100), nullable=False)
    area_name_nepali = db.Column(db.String(100), nullable=False)
    delivery_charge = db.Column(db.Float, default=0)
    min_order_amount = db.Column(db.Float, default=0)
    delivery_time_hours = db.Column(db.Integer, default=2)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<DeliveryArea {self.area_name}>'

class Invoice(db.Model):
    """
    Invoice model for order billing and accounting.
    Generates formal invoices for completed orders.
    """
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0)
    delivery_charge = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    order = db.relationship('Order', backref=db.backref('invoice', uselist=False))
    
    def generate_invoice_number(self):
        """Generate unique invoice number with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.invoice_number = f"INV{timestamp}"
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'