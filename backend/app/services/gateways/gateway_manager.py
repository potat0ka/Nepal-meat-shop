#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Gateway Manager
Unified interface for all payment gateways with modular architecture
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .khalti import KhaltiGateway
from .esewa import ESewaGateway

logger = logging.getLogger(__name__)

class PaymentGatewayManager:
    """
    Unified payment gateway manager that handles all payment providers.
    Provides a common interface for frontend and easy gateway management.
    """
    
    def __init__(self):
        self.gateways = {}
        self._initialize_gateways()
    
    def _initialize_gateways(self):
        """Initialize all available payment gateways."""
        try:
            # Initialize Khalti
            if self._is_gateway_enabled('khalti'):
                self.gateways['khalti'] = KhaltiGateway()
                logger.info("Khalti gateway initialized")
            
            # Initialize eSewa
            if self._is_gateway_enabled('esewa'):
                self.gateways['esewa'] = ESewaGateway()
                logger.info("eSewa gateway initialized")
            
            # Future gateways can be added here
            # if self._is_gateway_enabled('imepay'):
            #     self.gateways['imepay'] = IMEPayGateway()
            
            logger.info(f"Payment gateways initialized: {list(self.gateways.keys())}")
            
        except Exception as e:
            logger.error(f"Gateway initialization error: {str(e)}")
    
    def _is_gateway_enabled(self, gateway_name: str) -> bool:
        """Check if a gateway is enabled in environment variables."""
        env_var = f"{gateway_name.upper()}_ENABLED"
        return os.getenv(env_var, 'true').lower() == 'true'
    
    def get_available_gateways(self) -> List[Dict[str, Any]]:
        """
        Get list of available and configured payment gateways.
        
        Returns:
            List of gateway information
        """
        available_gateways = []
        
        for gateway_name, gateway_instance in self.gateways.items():
            if gateway_instance.is_configured():
                gateway_info = gateway_instance.get_config_info()
                gateway_info.update({
                    'display_name': self._get_gateway_display_name(gateway_name),
                    'logo_url': f'/static/images/payment/{gateway_name}.png',
                    'description': self._get_gateway_description(gateway_name)
                })
                available_gateways.append(gateway_info)
        
        return available_gateways
    
    def _get_gateway_display_name(self, gateway_name: str) -> str:
        """Get display name for gateway."""
        display_names = {
            'khalti': 'Khalti',
            'esewa': 'eSewa',
            'imepay': 'IME Pay',
            'connectips': 'ConnectIPS',
            'prabhupay': 'PrabhuPay'
        }
        return display_names.get(gateway_name, gateway_name.title())
    
    def _get_gateway_description(self, gateway_name: str) -> str:
        """Get description for gateway."""
        descriptions = {
            'khalti': 'Digital wallet payment / डिजिटल वालेट भुक्तानी',
            'esewa': 'Online payment system / अनलाइन भुक्तानी प्रणाली',
            'imepay': 'Mobile payment solution / मोबाइल भुक्तानी समाधान',
            'connectips': 'Bank transfer system / बैंक स्थानान्तरण प्रणाली',
            'prabhupay': 'Remittance payment / रेमिट्यान्स भुक्तानी'
        }
        return descriptions.get(gateway_name, 'Payment gateway / भुक्तानी गेटवे')
    
    def initiate_payment(self, gateway_name: str, amount: float, order_number: str, 
                        customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate payment through specified gateway.
        
        Args:
            gateway_name: Name of the payment gateway
            amount: Payment amount
            order_number: Unique order identifier
            customer_info: Customer information
        
        Returns:
            Payment initiation result
        """
        try:
            # Validate gateway
            if gateway_name not in self.gateways:
                return {
                    'success': False,
                    'message': f'भुक्तानी गेटवे उपलब्ध छैन / Payment gateway {gateway_name} not available',
                    'error': 'GATEWAY_NOT_FOUND'
                }
            
            gateway = self.gateways[gateway_name]
            
            # Check if gateway is configured
            if not gateway.is_configured():
                return {
                    'success': False,
                    'message': f'{gateway_name} भुक्तानी गेटवे कन्फिगर गरिएको छैन / {gateway_name} gateway not configured',
                    'error': 'GATEWAY_NOT_CONFIGURED'
                }
            
            # Validate amount
            if amount <= 0:
                return {
                    'success': False,
                    'message': 'अवैध रकम / Invalid amount',
                    'error': 'INVALID_AMOUNT'
                }
            
            # Log payment initiation
            logger.info(f"Initiating {gateway_name} payment: Order {order_number}, Amount NPR {amount}")
            
            # Initiate payment through gateway
            result = gateway.initiate_payment(amount, order_number, customer_info)
            
            # Add gateway name to result
            result['gateway'] = gateway_name
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Payment initiation error for {gateway_name}: {str(e)}")
            return {
                'success': False,
                'message': 'भुक्तानी सुरु गर्न सकिएन / Failed to initiate payment',
                'error': str(e),
                'gateway': gateway_name
            }
    
    def verify_payment(self, gateway_name: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment through specified gateway.
        
        Args:
            gateway_name: Name of the payment gateway
            payment_data: Payment verification data
        
        Returns:
            Payment verification result
        """
        try:
            # Validate gateway
            if gateway_name not in self.gateways:
                return {
                    'success': False,
                    'verified': False,
                    'message': f'भुक्तानी गेटवे उपलब्ध छैन / Payment gateway {gateway_name} not available',
                    'error': 'GATEWAY_NOT_FOUND'
                }
            
            gateway = self.gateways[gateway_name]
            
            # Log verification attempt
            logger.info(f"Verifying {gateway_name} payment: {payment_data.get('order_number', 'Unknown')}")
            
            # Verify payment through gateway
            result = gateway.verify_payment(payment_data)
            
            # Add gateway name and timestamp to result
            result['gateway'] = gateway_name
            result['verification_timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Payment verification error for {gateway_name}: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'message': 'भुक्तानी प्रमाणीकरणमा समस्या / Payment verification failed',
                'error': str(e),
                'gateway': gateway_name
            }
    
    def get_gateway_status(self, gateway_name: str) -> Dict[str, Any]:
        """
        Get status of a specific gateway.
        
        Args:
            gateway_name: Name of the payment gateway
        
        Returns:
            Gateway status information
        """
        if gateway_name not in self.gateways:
            return {
                'gateway': gateway_name,
                'available': False,
                'configured': False,
                'message': 'Gateway not found'
            }
        
        gateway = self.gateways[gateway_name]
        return {
            'gateway': gateway_name,
            'available': True,
            'configured': gateway.is_configured(),
            'config_info': gateway.get_config_info()
        }
    
    def get_all_gateway_status(self) -> Dict[str, Any]:
        """Get status of all gateways."""
        status = {
            'total_gateways': len(self.gateways),
            'configured_gateways': 0,
            'gateways': {}
        }
        
        for gateway_name in self.gateways:
            gateway_status = self.get_gateway_status(gateway_name)
            status['gateways'][gateway_name] = gateway_status
            
            if gateway_status['configured']:
                status['configured_gateways'] += 1
        
        return status
    
    def validate_payment_data(self, gateway_name: str, payment_data: Dict[str, Any]) -> bool:
        """
        Validate payment data for specific gateway.
        
        Args:
            gateway_name: Name of the payment gateway
            payment_data: Payment data to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            if gateway_name not in self.gateways:
                return False
            
            gateway = self.gateways[gateway_name]
            
            # Check if gateway has validation method
            if hasattr(gateway, 'validate_callback'):
                return gateway.validate_callback(payment_data)
            
            # Basic validation for required fields
            required_fields = ['order_number', 'amount']
            return all(field in payment_data for field in required_fields)
            
        except Exception as e:
            logger.error(f"Payment data validation error for {gateway_name}: {str(e)}")
            return False
    
    def get_supported_gateways(self) -> List[str]:
        """Get list of supported gateway names."""
        return list(self.gateways.keys())
    
    def is_gateway_available(self, gateway_name: str) -> bool:
        """Check if a gateway is available and configured."""
        return (gateway_name in self.gateways and 
                self.gateways[gateway_name].is_configured())

# Global instance
payment_manager = PaymentGatewayManager()