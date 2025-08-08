#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Gateways Package
Modular payment gateway system for Nepali payment providers
"""

from .khalti import KhaltiGateway
from .esewa import ESewaGateway
from .gateway_manager import PaymentGatewayManager, payment_manager

__all__ = [
    'KhaltiGateway',
    'ESewaGateway', 
    'PaymentGatewayManager',
    'payment_manager'
]

__version__ = '1.0.0'
__author__ = 'Nepal Meat Shop'
__description__ = 'Modular payment gateway system for Nepali payment providers'