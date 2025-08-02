from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin, db.Model):
    """User model for customer and admin accounts."""
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
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_cart_total(self):
        """Calculate total cart value."""
        total = 0
        for item in self.cart_items:
            total += item.quantity * item.product.price
        return total
    
    def get_cart_count(self):
        """Get total items in cart."""
        return sum(item.quantity for item in self.cart_items)

class Category(db.Model):
    """Product categories for meat cuts."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_nepali = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    """Product model for meat items."""
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
        """Calculate average rating from reviews."""
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    def get_freshness_label(self):
        """Get freshness label based on hours."""
        if self.freshness_hours <= 6:
            return "आज ताजा / Fresh Today"
        elif self.freshness_hours <= 24:
            return "हिजो काटिएको / Cut Yesterday"
        else:
            return "स्टक / Stock"
    
    def is_in_stock(self, quantity_kg):
        """Check if requested quantity is available."""
        return self.stock_kg >= quantity_kg

class Order(db.Model):
    """Order model for customer purchases."""
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
        """Generate unique order number."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.order_number = f"MO{timestamp}"
    
    def get_status_nepali(self):
        """Get order status in Nepali."""
        status_map = {
            'pending': 'पेन्डिङ / Pending',
            'confirmed': 'पुष्टि भयो / Confirmed',
            'processing': 'तयारी हुँदैछ / Processing',
            'out_for_delivery': 'डेलिभरीमा / Out for Delivery',
            'delivered': 'डेलिभर भयो / Delivered',
            'cancelled': 'रद्द भयो / Cancelled'
        }
        return status_map.get(self.status, self.status)

class OrderItem(db.Model):
    """Individual items in an order."""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class CartItem(db.Model):
    """Shopping cart items."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Quantity in kg
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_total_price(self):
        """Calculate total price for this cart item."""
        return self.quantity * self.product.price

class Review(db.Model):
    """Product reviews and ratings."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeliveryArea(db.Model):
    """Delivery areas and charges."""
    id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(100), nullable=False)
    area_name_nepali = db.Column(db.String(100), nullable=False)
    delivery_charge = db.Column(db.Float, default=0)
    min_order_amount = db.Column(db.Float, default=0)
    delivery_time_hours = db.Column(db.Integer, default=2)
    is_active = db.Column(db.Boolean, default=True)

class Invoice(db.Model):
    """Invoice model for order billing."""
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
        """Generate unique invoice number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.invoice_number = f"INV{timestamp}"

class SalesReport(db.Model):
    """Sales reports and analytics."""
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False)
    total_orders = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0)
    total_customers = db.Column(db.Integer, default=0)
    top_product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    avg_order_value = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    top_product = db.relationship('Product')

class StockAlert(db.Model):
    """Stock alert system for low inventory."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    threshold_kg = db.Column(db.Float, nullable=False, default=5.0)
    is_active = db.Column(db.Boolean, default=True)
    last_alert_sent = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    product = db.relationship('Product', backref='stock_alerts')
    
    def needs_alert(self):
        """Check if product stock is below threshold."""
        return self.product.stock_kg <= self.threshold_kg

class NotificationTemplate(db.Model):
    """Email/SMS notification templates."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # email, sms
    event = db.Column(db.String(50), nullable=False)  # order_placed, order_status_change, low_stock
    subject = db.Column(db.String(200))
    body_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationLog(db.Model):
    """Log of sent notifications."""
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('notification_template.id'))
    recipient = db.Column(db.String(100), nullable=False)  # email or phone
    type = db.Column(db.String(20), nullable=False)  # email, sms
    status = db.Column(db.String(20), default='sent')  # sent, failed, pending
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    
    # Relationships
    template = db.relationship('NotificationTemplate')
    order = db.relationship('Order')
