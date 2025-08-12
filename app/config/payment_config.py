#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Gateway Configuration
Secure configuration for payment gateways.
"""

import os
from typing import Dict, Any

class PaymentConfig:
    """Payment gateway configuration settings."""
    
    # eSewa Configuration
    ESEWA_MERCHANT_ID = os.environ.get('ESEWA_MERCHANT_ID')
    ESEWA_SECRET_KEY = os.environ.get('ESEWA_SECRET_KEY')
    ESEWA_SUCCESS_URL = os.environ.get('ESEWA_SUCCESS_URL', 'http://localhost:5000/payment/esewa/success')
    ESEWA_FAILURE_URL = os.environ.get('ESEWA_FAILURE_URL', 'http://localhost:5000/payment/esewa/failure')
    ESEWA_VERIFICATION_URL = os.environ.get('ESEWA_VERIFICATION_URL', 'https://uat.esewa.com.np/epay/transrec')
    
    # Khalti Configuration
    KHALTI_PUBLIC_KEY = os.environ.get('KHALTI_PUBLIC_KEY')
    KHALTI_SECRET_KEY = os.environ.get('KHALTI_SECRET_KEY')
    KHALTI_VERIFICATION_URL = os.environ.get('KHALTI_VERIFICATION_URL', 'https://khalti.com/api/v2/payment/verify/')
    KHALTI_SUCCESS_URL = os.environ.get('KHALTI_SUCCESS_URL', 'http://localhost:5000/payment/khalti/success')
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # General Payment Settings
    PAYMENT_TIMEOUT_MINUTES = int(os.environ.get('PAYMENT_TIMEOUT_MINUTES', '30'))
    PAYMENT_RETRY_ATTEMPTS = int(os.environ.get('PAYMENT_RETRY_ATTEMPTS', '3'))
    PAYMENT_LOG_LEVEL = os.environ.get('PAYMENT_LOG_LEVEL', 'INFO')
    
    # Security Settings
    PAYMENT_WEBHOOK_TIMEOUT = int(os.environ.get('PAYMENT_WEBHOOK_TIMEOUT', '10'))
    PAYMENT_VERIFICATION_TIMEOUT = int(os.environ.get('PAYMENT_VERIFICATION_TIMEOUT', '30'))
    
    @classmethod
    def get_gateway_config(cls, gateway: str) -> Dict[str, Any]:
        """Get configuration for a specific payment gateway."""
        configs = {
            'esewa': {
                'merchant_id': cls.ESEWA_MERCHANT_ID,
                'secret_key': cls.ESEWA_SECRET_KEY,
                'success_url': cls.ESEWA_SUCCESS_URL,
                'failure_url': cls.ESEWA_FAILURE_URL,
                'verification_url': cls.ESEWA_VERIFICATION_URL
            },
            'khalti': {
                'public_key': cls.KHALTI_PUBLIC_KEY,
                'secret_key': cls.KHALTI_SECRET_KEY,
                'verification_url': cls.KHALTI_VERIFICATION_URL,
                'success_url': cls.KHALTI_SUCCESS_URL
            },
            'stripe': {
                'publishable_key': cls.STRIPE_PUBLISHABLE_KEY,
                'secret_key': cls.STRIPE_SECRET_KEY,
                'webhook_secret': cls.STRIPE_WEBHOOK_SECRET
            }
        }
        return configs.get(gateway, {})
    
    @classmethod
    def is_gateway_enabled(cls, gateway: str) -> bool:
        """Check if a payment gateway is properly configured."""
        config = cls.get_gateway_config(gateway)
        
        if gateway == 'esewa':
            return bool(config.get('merchant_id') and config.get('secret_key'))
        elif gateway == 'khalti':
            return bool(config.get('public_key') and config.get('secret_key'))
        elif gateway == 'stripe':
            return bool(config.get('secret_key') and config.get('webhook_secret'))
        
        return False
    
    @classmethod
    def get_enabled_gateways(cls) -> list:
        """Get list of enabled payment gateways."""
        gateways = ['esewa', 'khalti', 'stripe']
        return [gateway for gateway in gateways if cls.is_gateway_enabled(gateway)]

# Environment-specific configurations
class DevelopmentPaymentConfig(PaymentConfig):
    """Development environment payment configuration."""
    
    # Use test/sandbox URLs for development
    ESEWA_VERIFICATION_URL = 'https://uat.esewa.com.np/epay/transrec'
    KHALTI_VERIFICATION_URL = 'https://khalti.com/api/v2/payment/verify/'

class ProductionPaymentConfig(PaymentConfig):
    """Production environment payment configuration."""
    
    # Use live URLs for production
    ESEWA_VERIFICATION_URL = 'https://esewa.com.np/epay/transrec'
    KHALTI_VERIFICATION_URL = 'https://khalti.com/api/v2/payment/verify/'
    
    # Enhanced security for production
    PAYMENT_WEBHOOK_TIMEOUT = 5
    PAYMENT_VERIFICATION_TIMEOUT = 15

class TestingPaymentConfig(PaymentConfig):
    """Testing environment payment configuration."""
    
    # Mock configurations for testing
    ESEWA_MERCHANT_ID = 'TEST_MERCHANT'
    ESEWA_SECRET_KEY = 'TEST_SECRET'
    KHALTI_PUBLIC_KEY = 'test_public_key'
    KHALTI_SECRET_KEY = 'test_secret_key'
    STRIPE_SECRET_KEY = 'sk_test_mock'
    STRIPE_WEBHOOK_SECRET = 'whsec_test_mock'

# Configuration mapping
payment_config = {
    'development': DevelopmentPaymentConfig,
    'production': ProductionPaymentConfig,
    'testing': TestingPaymentConfig,
    'default': DevelopmentPaymentConfig
}