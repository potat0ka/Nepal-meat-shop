#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Khalti Payment Gateway Integration
Official Khalti Payment Gateway implementation following docs.khalti.com
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class KhaltiGateway:
    """
    Khalti Payment Gateway integration following official documentation.
    Supports both sandbox and production environments.
    """
    
    def __init__(self):
        self.environment = os.getenv('PAYMENT_ENVIRONMENT', 'sandbox')
        self.public_key = os.getenv('KHALTI_PUBLIC_KEY')
        self.secret_key = os.getenv('KHALTI_SECRET_KEY')
        
        # Set URLs based on environment
        if self.environment == 'production':
            self.initiate_url = os.getenv('KHALTI_PRODUCTION_URL')
            self.verification_url = os.getenv('KHALTI_VERIFICATION_PRODUCTION_URL')
        else:
            self.initiate_url = os.getenv('KHALTI_SANDBOX_URL')
            self.verification_url = os.getenv('KHALTI_VERIFICATION_SANDBOX_URL')
        
        self.success_url = os.getenv('KHALTI_SUCCESS_URL')
        self.failure_url = os.getenv('KHALTI_FAILURE_URL')
        
        # Validate configuration
        if not all([self.public_key, self.secret_key, self.initiate_url]):
            raise ValueError("Khalti configuration incomplete. Check environment variables.")
    
    def initiate_payment(self, amount: float, order_number: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate Khalti payment following official API documentation.
        
        Args:
            amount: Payment amount in NPR
            order_number: Unique order identifier
            customer_info: Customer details (name, email, phone)
        
        Returns:
            Dict containing payment initiation response
        """
        try:
            # Convert amount to paisa (Khalti uses paisa as base unit)
            amount_paisa = int(amount * 100)
            
            # Prepare payment data according to Khalti API
            payment_data = {
                "return_url": self.success_url,
                "website_url": "http://127.0.0.1:5000",
                "amount": amount_paisa,
                "purchase_order_id": order_number,
                "purchase_order_name": f"Nepal Meat Shop Order {order_number}",
                "customer_info": {
                    "name": customer_info.get('name', 'Customer'),
                    "email": customer_info.get('email', 'customer@example.com'),
                    "phone": customer_info.get('phone', '9800000000')
                }
            }
            
            # Set headers for API request
            headers = {
                'Authorization': f'Key {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Initiating Khalti payment for order {order_number}, amount: NPR {amount}")
            
            # Make API request to Khalti
            response = requests.post(
                self.initiate_url,
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                return {
                    'success': True,
                    'payment_url': response_data.get('payment_url'),
                    'pidx': response_data.get('pidx'),
                    'expires_at': response_data.get('expires_at'),
                    'message': 'Khalti भुक्तानीमा रिडाइरेक्ट गर्दै... / Redirecting to Khalti payment...',
                    'gateway': 'khalti'
                }
            else:
                logger.error(f"Khalti payment initiation failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': 'Khalti भुक्तानी सुरु गर्न सकिएन / Failed to initiate Khalti payment',
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti API request failed: {str(e)}")
            return {
                'success': False,
                'message': 'Khalti सेवामा समस्या / Khalti service unavailable',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Khalti payment initiation error: {str(e)}")
            return {
                'success': False,
                'message': 'भुक्तानी प्रक्रियामा समस्या / Payment processing error',
                'error': str(e)
            }
    
    def verify_payment(self, pidx: str) -> Dict[str, Any]:
        """
        Verify Khalti payment using pidx (payment identifier).
        
        Args:
            pidx: Payment identifier returned from Khalti
        
        Returns:
            Dict containing verification result
        """
        try:
            headers = {
                'Authorization': f'Key {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare verification data
            verification_data = {
                "pidx": pidx
            }
            
            logger.info(f"Verifying Khalti payment with pidx: {pidx}")
            
            # Make verification request
            response = requests.post(
                self.verification_url,
                json=verification_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check payment status
                if response_data.get('status') == 'Completed':
                    return {
                        'success': True,
                        'verified': True,
                        'transaction_id': response_data.get('transaction_id'),
                        'order_number': response_data.get('purchase_order_id'),
                        'amount': response_data.get('total_amount', 0) / 100,  # Convert from paisa
                        'fee': response_data.get('fee', 0) / 100,
                        'status': response_data.get('status'),
                        'message': 'Khalti भुक्तानी सफल भयो / Khalti payment verified successfully'
                    }
                else:
                    return {
                        'success': False,
                        'verified': False,
                        'status': response_data.get('status'),
                        'message': f'Khalti भुक्तानी अपूर्ण: {response_data.get("status")} / Khalti payment incomplete'
                    }
            else:
                logger.error(f"Khalti verification failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'verified': False,
                    'message': 'Khalti भुक्तानी प्रमाणीकरण असफल / Khalti payment verification failed',
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti verification request failed: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'Khalti प्रमाणीकरण सेवामा समस्या / Khalti verification service unavailable',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Khalti verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'भुक्तानी प्रमाणीकरणमा समस्या / Payment verification error',
                'error': str(e)
            }
    
    def get_payment_status(self, pidx: str) -> str:
        """
        Get current payment status for a given pidx.
        
        Args:
            pidx: Payment identifier
        
        Returns:
            Payment status string
        """
        verification_result = self.verify_payment(pidx)
        if verification_result.get('success'):
            return verification_result.get('status', 'Unknown')
        return 'Failed'
    
    def is_configured(self) -> bool:
        """Check if Khalti gateway is properly configured."""
        return all([
            self.public_key,
            self.secret_key,
            self.initiate_url,
            self.verification_url
        ])
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get gateway configuration information (without sensitive data)."""
        return {
            'gateway': 'khalti',
            'environment': self.environment,
            'configured': self.is_configured(),
            'public_key': self.public_key[:20] + '...' if self.public_key else None,
            'initiate_url': self.initiate_url,
            'success_url': self.success_url
        }