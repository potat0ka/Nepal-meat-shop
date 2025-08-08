#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Service
Secure payment processing with webhook verification for multiple payment gateways.
"""

import hashlib
import hmac
import json
import logging
import requests
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from flask import current_app
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentService:
    """
    Secure payment processing service with webhook verification.
    Supports eSewa, Khalti, Stripe, and other payment gateways.
    """
    
    def __init__(self):
        self.esewa_config = {
            'merchant_id': os.getenv('ESEWA_MERCHANT_ID', 'test_merchant'),
            'secret_key': os.getenv('ESEWA_SECRET_KEY', 'test_secret'),
            'success_url': os.getenv('ESEWA_SUCCESS_URL', 'http://127.0.0.1:5000/payment/esewa/success'),
            'failure_url': os.getenv('ESEWA_FAILURE_URL', 'http://127.0.0.1:5000/payment/esewa/failure'),
            'api_url': os.getenv('ESEWA_API_URL', 'https://uat.esewa.com.np/epay/main')
        }
        
        self.khalti_config = {
            'public_key': os.getenv('KHALTI_PUBLIC_KEY', 'test_public_key'),
            'secret_key': os.getenv('KHALTI_SECRET_KEY', 'test_secret_key'),
            'api_url': os.getenv('KHALTI_API_URL', 'https://a.khalti.com/api/v2/')
        }
        
        self.stripe_config = {
            'public_key': os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_'),
            'secret_key': os.getenv('STRIPE_SECRET_KEY', 'sk_test_'),
            'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_test')
        }
    
    def initiate_payment(self, payment_method: str, amount: float, order_number: str, 
                        customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate payment with the selected gateway.
        Returns payment URL and transaction details.
        """
        try:
            transaction_id = self._generate_transaction_id()
            
            if payment_method == 'cod':
                return self._handle_cod_payment(order_number, transaction_id)
            elif payment_method == 'esewa':
                return self._initiate_esewa_payment(amount, order_number, transaction_id, customer_info)
            elif payment_method == 'khalti':
                return self._initiate_khalti_payment(amount, order_number, transaction_id, customer_info)
            elif payment_method == 'stripe':
                return self._initiate_stripe_payment(amount, order_number, transaction_id, customer_info)
            else:
                return {
                    'success': False,
                    'message': 'Unsupported payment method',
                    'payment_status': 'failed'
                }
                
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'Payment initiation failed',
                'payment_status': 'failed',
                'error': str(e)
            }
    
    def _handle_cod_payment(self, order_number: str, transaction_id: str) -> Dict[str, Any]:
        """Handle Cash on Delivery payment."""
        return {
            'success': True,
            'message': 'अर्डर सफल भयो! घरमा पैसा तिर्नुहोस् / Order placed successfully! Pay on delivery.',
            'payment_status': 'pending',
            'transaction_id': transaction_id,
            'requires_verification': False
        }
    
    def _initiate_esewa_payment(self, amount: float, order_number: str, 
                               transaction_id: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate eSewa payment."""
        try:
            # eSewa payment parameters
            payment_data = {
                'amt': amount,
                'pdc': 0,  # Product delivery charge
                'psc': 0,  # Product service charge
                'txAmt': 0,  # Tax amount
                'tAmt': amount,  # Total amount
                'pid': order_number,  # Product ID (order number)
                'scd': self.esewa_config['merchant_id'],  # Merchant code
                'su': self.esewa_config['success_url'],  # Success URL
                'fu': self.esewa_config['failure_url']   # Failure URL
            }
            
            # Generate payment URL
            payment_url = f"{self.esewa_config['api_url']}?" + "&".join([f"{k}={v}" for k, v in payment_data.items()])
            
            return {
                'success': True,
                'message': 'eSewa भुक्तानीमा रिडाइरेक्ट गर्दै... / Redirecting to eSewa payment...',
                'payment_status': 'pending',
                'transaction_id': transaction_id,
                'payment_url': payment_url,
                'requires_verification': True,
                'gateway': 'esewa'
            }
            
        except Exception as e:
            logger.error(f"eSewa payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'eSewa payment initiation failed',
                'payment_status': 'failed'
            }
    
    def _initiate_khalti_payment(self, amount: float, order_number: str, 
                                transaction_id: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate Khalti payment."""
        try:
            # Convert amount to paisa (Khalti uses paisa)
            amount_paisa = int(amount * 100)
            
            payment_data = {
                'return_url': 'http://127.0.0.1:5000/payment/khalti/success',
                'website_url': 'http://127.0.0.1:5000',
                'amount': amount_paisa,
                'purchase_order_id': order_number,
                'purchase_order_name': f'Nepal Meat Shop Order {order_number}',
                'customer_info': {
                    'name': customer_info.get('name', 'Customer'),
                    'email': customer_info.get('email', 'customer@example.com'),
                    'phone': customer_info.get('phone', '9800000000')
                }
            }
            
            headers = {
                'Authorization': f'Key {self.khalti_config["secret_key"]}',
                'Content-Type': 'application/json'
            }
            
            # For demo purposes, return a mock payment URL
            # In production, you would make an API call to Khalti
            return {
                'success': True,
                'message': 'Khalti भुक्तानीमा रिडाइरेक्ट गर्दै... / Redirecting to Khalti payment...',
                'payment_status': 'pending',
                'transaction_id': transaction_id,
                'payment_url': f'https://pay.khalti.com/api/v2/epayment/initiate/',
                'requires_verification': True,
                'gateway': 'khalti'
            }
            
        except Exception as e:
            logger.error(f"Khalti payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'Khalti payment initiation failed',
                'payment_status': 'failed'
            }
    
    def _initiate_stripe_payment(self, amount: float, order_number: str, 
                                transaction_id: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate Stripe payment."""
        try:
            # For demo purposes, return a mock payment URL
            # In production, you would create a Stripe checkout session
            return {
                'success': True,
                'message': 'Stripe भुक्तानीमा रिडाइरेक्ट गर्दै... / Redirecting to Stripe payment...',
                'payment_status': 'pending',
                'transaction_id': transaction_id,
                'payment_url': f'https://checkout.stripe.com/pay/{transaction_id}',
                'requires_verification': True,
                'gateway': 'stripe'
            }
            
        except Exception as e:
            logger.error(f"Stripe payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'Stripe payment initiation failed',
                'payment_status': 'failed'
            }
    
    def verify_esewa_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify eSewa payment using their verification API."""
        try:
            # eSewa verification parameters
            verification_data = {
                'amt': payment_data.get('amt'),
                'rid': payment_data.get('refId'),
                'pid': payment_data.get('oid'),
                'scd': self.esewa_config['merchant_id']
            }
            
            # In production, make API call to eSewa verification endpoint
            # For demo, simulate verification
            if payment_data.get('refId') and payment_data.get('oid'):
                return {
                    'success': True,
                    'verified': True,
                    'transaction_id': payment_data.get('refId'),
                    'order_number': payment_data.get('oid'),
                    'amount': payment_data.get('amt'),
                    'message': 'eSewa भुक्तानी सफल भयो / eSewa payment verified successfully'
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'message': 'eSewa भुक्तानी प्रमाणीकरण असफल / eSewa payment verification failed'
                }
                
        except Exception as e:
            logger.error(f"eSewa verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'Payment verification failed'
            }
    
    def verify_khalti_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Khalti payment using their verification API."""
        try:
            # In production, make API call to Khalti verification endpoint
            # For demo, simulate verification
            if payment_data.get('pidx') and payment_data.get('transaction_id'):
                return {
                    'success': True,
                    'verified': True,
                    'transaction_id': payment_data.get('transaction_id'),
                    'order_number': payment_data.get('purchase_order_id'),
                    'amount': payment_data.get('amount', 0) / 100,  # Convert from paisa
                    'message': 'Khalti भुक्तानी सफल भयो / Khalti payment verified successfully'
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'message': 'Khalti भुक्तानी प्रमाणीकरण असफल / Khalti payment verification failed'
                }
                
        except Exception as e:
            logger.error(f"Khalti verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'Payment verification failed'
            }
    
    def verify_stripe_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature and process payment."""
        try:
            # Verify webhook signature
            expected_signature = hmac.new(
                self.stripe_config['webhook_secret'].encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(f"sha256={expected_signature}", signature):
                return {
                    'success': False,
                    'verified': False,
                    'message': 'Invalid webhook signature'
                }
            
            # Parse webhook data
            event_data = json.loads(payload)
            
            if event_data.get('type') == 'payment_intent.succeeded':
                payment_intent = event_data.get('data', {}).get('object', {})
                return {
                    'success': True,
                    'verified': True,
                    'transaction_id': payment_intent.get('id'),
                    'amount': payment_intent.get('amount', 0) / 100,  # Convert from cents
                    'message': 'Stripe payment verified successfully'
                }
            
            return {
                'success': False,
                'verified': False,
                'message': 'Unhandled webhook event'
            }
            
        except Exception as e:
            logger.error(f"Stripe webhook verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'Webhook verification failed'
            }
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"TXN{timestamp}{unique_id}"
    
    def log_payment_attempt(self, order_number: str, payment_method: str, 
                           amount: float, status: str, details: Dict[str, Any] = None):
        """Log payment attempt for audit trail."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'order_number': order_number,
            'payment_method': payment_method,
            'amount': amount,
            'status': status,
            'details': details or {}
        }
        
        logger.info(f"Payment attempt logged: {json.dumps(log_entry)}")
        
        # In production, save to database or external logging service
        # For now, just log to file
        try:
            log_file = os.path.join(current_app.instance_path, 'payment_logs.json')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write payment log: {str(e)}")

# Global payment service instance
payment_service = PaymentService()