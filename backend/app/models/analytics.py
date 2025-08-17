#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Analytics & Notification Models
Sales reporting, analytics, and notification system models.
"""

from datetime import datetime
# SQLAlchemy removed - using MongoDB models instead

class SalesReport(db.Model):
    """
    Sales reports and analytics for business insights.
    Tracks daily sales performance and customer metrics.
    """
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
    
    def __repr__(self):
        return f'<SalesReport {self.report_date}>'

class NotificationTemplate(db.Model):
    """
    Email/SMS notification templates for automated messaging.
    Supports dynamic content with template variables.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # email, sms
    event = db.Column(db.String(50), nullable=False)  # order_placed, order_status_change, low_stock
    subject = db.Column(db.String(200))
    body_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.name}>'

class NotificationLog(db.Model):
    """
    Log of sent notifications for tracking and debugging.
    Maintains history of all automated communications.
    """
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
    
    def __repr__(self):
        return f'<NotificationLog {self.type} to {self.recipient}>'