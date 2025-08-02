"""
Notification utility functions for sending emails and SMS notifications.
This module handles all notification-related functionality for the meat shop eCommerce platform.
"""

import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from models import NotificationLog, NotificationTemplate

class NotificationService:
    """Service class to handle email and SMS notifications."""
    
    def __init__(self):
        """Initialize notification service with configuration."""
        # Email configuration (using environment variables for security)
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@meatshop.np')
        
        # SMS configuration (can be extended with actual SMS service)
        self.sms_api_key = os.environ.get('SMS_API_KEY', '')
        self.sms_sender_name = os.environ.get('SMS_SENDER_NAME', 'MeatShop')
    
    def send_email(self, to_email, subject, body_text, body_html=None):
        """
        Send email notification to the specified recipient.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject line
            body_text (str): Plain text body content
            body_html (str): HTML body content (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create text and HTML parts
            text_part = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(text_part)
            
            if body_html:
                html_part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Send email via SMTP
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                
                current_app.logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                current_app.logger.warning("SMTP credentials not configured. Email not sent.")
                # In development, just log the email content
                current_app.logger.info(f"EMAIL CONTENT:\nTo: {to_email}\nSubject: {subject}\nBody: {body_text}")
                return True
                
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_sms(self, phone_number, message):
        """
        Send SMS notification to the specified phone number.
        
        Args:
            phone_number (str): Recipient phone number
            message (str): SMS message content
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            # For development, just log the SMS content
            # In production, integrate with actual SMS service like:
            # - Sparrow SMS (Nepal)
            # - Khalti SMS
            # - Any other SMS gateway
            
            if self.sms_api_key:
                # TODO: Implement actual SMS sending logic here
                # Example structure for SMS API integration:
                # response = requests.post('https://sms-api.example.com/send', {
                #     'api_key': self.sms_api_key,
                #     'to': phone_number,
                #     'message': message,
                #     'sender': self.sms_sender_name
                # })
                pass
            
            # For now, just log the SMS content
            current_app.logger.info(f"SMS CONTENT:\nTo: {phone_number}\nMessage: {message}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def send_order_confirmation_email(self, order):
        """
        Send order confirmation email to customer.
        
        Args:
            order: Order object containing order details
        """
        # Get email template or use default
        template = NotificationTemplate.query.filter_by(
            event='order_placed', 
            type='email', 
            is_active=True
        ).first()
        
        if template:
            subject = template.subject
            body_template = template.body_template
        else:
            subject = "Order Confirmation - Nepal Meat Shop"
            body_template = """
            Dear {customer_name},
            
            Thank you for your order! Your order #{order_number} has been received and is being processed.
            
            Order Details:
            - Order Number: {order_number}
            - Total Amount: रू {total_amount}
            - Payment Method: {payment_method}
            - Delivery Address: {delivery_address}
            
            We will notify you once your order is ready for delivery.
            
            Thank you for choosing Nepal Meat Shop!
            
            Best regards,
            Nepal Meat Shop Team
            """
        
        # Replace template variables
        email_body = body_template.format(
            customer_name=order.customer.full_name,
            order_number=order.order_number,
            total_amount=f"{order.total_amount:.0f}",
            payment_method=order.payment_method.upper(),
            delivery_address=order.delivery_address
        )
        
        # Send email
        success = self.send_email(
            to_email=order.customer.email,
            subject=subject,
            body_text=email_body
        )
        
        # Log notification
        self._log_notification(
            template_id=template.id if template else None,
            recipient=order.customer.email,
            notification_type='email',
            status='sent' if success else 'failed',
            order_id=order.id
        )
        
        return success
    
    def send_order_status_update_email(self, order, old_status, new_status):
        """
        Send order status update email to customer.
        
        Args:
            order: Order object
            old_status: Previous order status
            new_status: New order status
        """
        status_messages = {
            'confirmed': 'Your order has been confirmed and is being prepared.',
            'processing': 'Your order is currently being processed.',
            'out_for_delivery': 'Your order is out for delivery!',
            'delivered': 'Your order has been delivered successfully.',
            'cancelled': 'Your order has been cancelled.'
        }
        
        subject = f"Order Update - {order.order_number} - Nepal Meat Shop"
        
        email_body = f"""
        Dear {order.customer.full_name},
        
        Your order #{order.order_number} status has been updated.
        
        Status: {new_status.replace('_', ' ').title()}
        {status_messages.get(new_status, '')}
        
        Order Details:
        - Order Number: {order.order_number}
        - Total Amount: रू {order.total_amount:.0f}
        - Payment Method: {order.payment_method.upper()}
        
        Thank you for choosing Nepal Meat Shop!
        
        Best regards,
        Nepal Meat Shop Team
        """
        
        success = self.send_email(
            to_email=order.customer.email,
            subject=subject,
            body_text=email_body
        )
        
        # Log notification
        self._log_notification(
            recipient=order.customer.email,
            notification_type='email',
            status='sent' if success else 'failed',
            order_id=order.id
        )
        
        return success
    
    def send_admin_new_order_notification(self, order):
        """
        Send notification to admin when new order is received.
        
        Args:
            order: Order object containing order details
        """
        # Admin email (can be configured in environment variables)
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@meatshop.np')
        
        subject = f"New Order Received - {order.order_number}"
        
        email_body = f"""
        New order received on Nepal Meat Shop!
        
        Order Details:
        - Order Number: {order.order_number}
        - Customer: {order.customer.full_name} ({order.customer.email})
        - Phone: {order.delivery_phone}
        - Total Amount: रू {order.total_amount:.0f}
        - Payment Method: {order.payment_method.upper()}
        - Delivery Address: {order.delivery_address}
        
        Order Items:
        """
        
        for item in order.order_items:
            email_body += f"- {item.product.name}: {item.quantity_kg}kg @ रू {item.price_per_kg}/kg = रू {item.total_price:.0f}\n"
        
        email_body += f"""
        
        Special Instructions: {order.special_instructions or 'None'}
        
        Please process this order promptly.
        
        Login to admin panel: {os.environ.get('ADMIN_URL', 'https://your-domain.com/admin')}
        """
        
        success = self.send_email(
            to_email=admin_email,
            subject=subject,
            body_text=email_body
        )
        
        # Log notification
        self._log_notification(
            recipient=admin_email,
            notification_type='email',
            status='sent' if success else 'failed',
            order_id=order.id
        )
        
        return success
    
    def send_low_stock_alert(self, product):
        """
        Send low stock alert to admin.
        
        Args:
            product: Product object with low stock
        """
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@meatshop.np')
        
        subject = f"Low Stock Alert - {product.name}"
        
        email_body = f"""
        Low Stock Alert!
        
        Product: {product.name} ({product.name_nepali})
        Current Stock: {product.stock_kg}kg
        Category: {product.category.name}
        
        This product is running low on stock. Please restock soon to avoid stockouts.
        
        Login to admin panel to update stock: {os.environ.get('ADMIN_URL', 'https://your-domain.com/admin')}
        """
        
        success = self.send_email(
            to_email=admin_email,
            subject=subject,
            body_text=email_body
        )
        
        # Log notification
        self._log_notification(
            recipient=admin_email,
            notification_type='email',
            status='sent' if success else 'failed'
        )
        
        return success
    
    def _log_notification(self, recipient, notification_type, status, template_id=None, order_id=None):
        """
        Log notification in database for tracking.
        
        Args:
            recipient: Email or phone number
            notification_type: 'email' or 'sms'
            status: 'sent', 'failed', or 'pending'
            template_id: ID of notification template used (optional)
            order_id: ID of related order (optional)
        """
        try:
            from app import db
            
            log_entry = NotificationLog(
                template_id=template_id,
                recipient=recipient,
                type=notification_type,
                status=status,
                order_id=order_id
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Failed to log notification: {str(e)}")

# Create global notification service instance
notification_service = NotificationService()

def send_order_confirmation(order):
    """Convenience function to send order confirmation."""
    return notification_service.send_order_confirmation_email(order)

def send_order_status_update(order, old_status, new_status):
    """Convenience function to send order status update."""
    return notification_service.send_order_status_update_email(order, old_status, new_status)

def send_admin_new_order_notification(order):
    """Convenience function to send admin notification."""
    return notification_service.send_admin_new_order_notification(order)

def send_low_stock_alert(product):
    """Convenience function to send low stock alert."""
    return notification_service.send_low_stock_alert(product)
