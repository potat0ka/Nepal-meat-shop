#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - eSewa Payment Gateway Integration
eSewa Epay-v2 implementation with sandbox and production support
"""

import os
import requests
import hashlib
import hmac
import base64
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ESewaGateway:
    """
    eSewa Payment Gateway integration using Epay-v2 API.
    Supports both sandbox and production environments.
    """
    
    def __init__(self):
        self.environment = os.getenv('ESEWA_ENVIRONMENT', os.getenv('PAYMENT_ENVIRONMENT', 'sandbox'))
        self.merchant_id = os.getenv('ESEWA_MERCHANT_CODE')
        self.secret_key = os.getenv('ESEWA_SECRET_KEY')
        self.client_id = os.getenv('ESEWA_CLIENT_ID')
        self.client_secret = os.getenv('ESEWA_CLIENT_SECRET')
        
        # Set URLs based on environment
        if self.environment == 'production':
            self.payment_url = os.getenv('ESEWA_PRODUCTION_URL')
            self.verification_url = os.getenv('ESEWA_VERIFICATION_PRODUCTION_URL')
        else:
            self.payment_url = os.getenv('ESEWA_SANDBOX_URL')
            self.verification_url = os.getenv('ESEWA_VERIFICATION_SANDBOX_URL')
        
        self.success_url = os.getenv('ESEWA_SUCCESS_URL')
        self.failure_url = os.getenv('ESEWA_FAILURE_URL')
        
        # Validate configuration
        if not all([self.merchant_id, self.secret_key]):
            raise ValueError("eSewa configuration incomplete. Check environment variables.")
    
    def initiate_payment(self, amount: float, order_number: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate eSewa payment using Epay-v2 form submission.
        
        Args:
            amount: Payment amount in NPR
            order_number: Unique order identifier
            customer_info: Customer details
        
        Returns:
            Dict containing payment form data and URL
        """
        try:
            # Prepare payment parameters
            payment_data = {
                'amt': str(amount),
                'pdc': '0',  # Product delivery charge
                'psc': '0',  # Product service charge
                'txAmt': '0',  # Tax amount
                'tAmt': str(amount),  # Total amount
                'pid': order_number,  # Product ID (order number)
                'scd': self.merchant_id,  # Service code (merchant ID)
                'su': self.success_url,  # Success URL
                'fu': self.failure_url   # Failure URL
            }
            
            logger.info(f"Initiating eSewa payment for order {order_number}, amount: NPR {amount}")
            
            # Generate payment form HTML for frontend
            form_html = self._generate_payment_form(payment_data)
            
            return {
                'success': True,
                'payment_url': self.payment_url,
                'form_data': payment_data,
                'form_html': form_html,
                'message': 'eSewa भुक्तानीमा रिडाइरेक्ट गर्दै... / Redirecting to eSewa payment...',
                'gateway': 'esewa'
            }
            
        except Exception as e:
            logger.error(f"eSewa payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'eSewa भुक्तानी सुरु गर्न सकिएन / Failed to initiate eSewa payment',
                'error': str(e)
            }
    
    def verify_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify eSewa payment using their verification API.
        
        Args:
            payment_data: Payment response data from eSewa
        
        Returns:
            Dict containing verification result
        """
        try:
            # Extract verification parameters
            verification_params = {
                'amt': payment_data.get('amt'),
                'rid': payment_data.get('refId'),  # Reference ID from eSewa
                'pid': payment_data.get('oid'),    # Order ID
                'scd': self.merchant_id
            }
            
            logger.info(f"Verifying eSewa payment: {verification_params}")
            
            # Make verification request
            response = requests.post(
                self.verification_url,
                data=verification_params,
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.text.strip()
                
                # eSewa returns "Success" for successful verification
                if response_text.lower() == 'success':
                    return {
                        'success': True,
                        'verified': True,
                        'transaction_id': payment_data.get('refId'),
                        'order_number': payment_data.get('oid'),
                        'amount': float(payment_data.get('amt', 0)),
                        'message': 'eSewa भुक्तानी सफल भयो / eSewa payment verified successfully'
                    }
                else:
                    logger.warning(f"eSewa verification failed: {response_text}")
                    return {
                        'success': False,
                        'verified': False,
                        'message': 'eSewa भुक्तानी प्रमाणीकरण असफल / eSewa payment verification failed',
                        'error': response_text
                    }
            else:
                logger.error(f"eSewa verification request failed: {response.status_code}")
                return {
                    'success': False,
                    'verified': False,
                    'message': 'eSewa प्रमाणीकरण सेवामा समस्या / eSewa verification service error'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"eSewa verification request failed: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'eSewa प्रमाणीकरण सेवामा समस्या / eSewa verification service unavailable',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"eSewa verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'भुक्तानी प्रमाणीकरणमा समस्या / Payment verification error',
                'error': str(e)
            }
    
    def _generate_payment_form(self, payment_data: Dict[str, str]) -> str:
        """
        Generate HTML form for eSewa payment submission.
        
        Args:
            payment_data: Payment parameters
        
        Returns:
            HTML form string
        """
        form_fields = ""
        for key, value in payment_data.items():
            form_fields += f'<input type="hidden" name="{key}" value="{value}">\n'
        
        form_html = f"""
        <form id="esewaForm" action="{self.payment_url}" method="POST">
            {form_fields}
        </form>
        <script>
            document.getElementById('esewaForm').submit();
        </script>
        """
        
        return form_html
    
    def generate_signature(self, data: str) -> str:
        """
        Generate HMAC signature for eSewa API requests.
        
        Args:
            data: Data to sign
        
        Returns:
            Base64 encoded signature
        """
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def validate_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        Validate eSewa callback data integrity.
        
        Args:
            callback_data: Callback data from eSewa
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check required fields
            required_fields = ['oid', 'amt', 'refId']
            return all(field in callback_data for field in required_fields)
        except Exception as e:
            logger.error(f"eSewa callback validation error: {str(e)}")
            return False
    
    def is_configured(self) -> bool:
        """Check if eSewa gateway is properly configured."""
        return all([
            self.merchant_id,
            self.secret_key,
            self.payment_url,
            self.verification_url
        ])
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get gateway configuration information (without sensitive data)."""
        return {
            'gateway': 'esewa',
            'environment': self.environment,
            'configured': self.is_configured(),
            'merchant_id': self.merchant_id,
            'payment_url': self.payment_url,
            'success_url': self.success_url
        }
    
    def get_test_credentials(self) -> Dict[str, str]:
        """Get test credentials for sandbox testing."""
        if self.environment == 'sandbox':
            return {
                'test_ids': '9806800001 to 9806800005',
                'password': 'Nepal@123',
                'mpin': '1122',
                'merchant_code': 'EPAYTEST',
                'token': '123456'
            }
        return {}