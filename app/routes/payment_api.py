#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment API Routes
Unified payment gateway API endpoints for frontend integration
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.exceptions import BadRequest

from app.services.gateways import payment_manager
from app.models.mongo_models import MongoOrder as Order

logger = logging.getLogger(__name__)

# Create blueprint
payment_api = Blueprint('payment_api', __name__, url_prefix='/api/payment')

@payment_api.route('/gateways', methods=['GET'])
def get_available_gateways():
    """
    Get list of available payment gateways.
    
    Returns:
        JSON response with available gateways
    """
    try:
        gateways = payment_manager.get_available_gateways()
        
        return jsonify({
            'success': True,
            'gateways': gateways,
            'total': len(gateways)
        })
        
    except Exception as e:
        logger.error(f"Error fetching gateways: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'गेटवे जानकारी प्राप्त गर्न सकिएन / Failed to fetch gateway information',
            'error': str(e)
        }), 500

@payment_api.route('/initiate', methods=['POST'])
def initiate_payment():
    """
    Initiate payment through specified gateway.
    
    Expected JSON payload:
    {
        "gateway": "khalti|esewa",
        "order_number": "ORD123456",
        "amount": 1500.0,
        "customer_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "9841234567"
        }
    }
    
    Returns:
        JSON response with payment initiation result
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'JSON डेटा आवश्यक छ / JSON data required'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['gateway', 'order_number', 'amount']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'आवश्यक फिल्डहरू छुटेका छन् / Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        gateway_name = data['gateway'].lower()
        order_number = data['order_number']
        amount = float(data['amount'])
        customer_info = data.get('customer_info', {})
        
        # Validate order exists
        order = Order.find_by_order_number(order_number)
        if not order:
            return jsonify({
                'success': False,
                'message': 'अर्डर फेला परेन / Order not found'
            }), 404
        
        # Check if order is already paid
        if order.get('payment_status') == 'paid':
            return jsonify({
                'success': False,
                'message': 'यो अर्डर पहिले नै भुक्तानी भइसकेको छ / Order already paid'
            }), 400
        
        # Validate amount matches order total
        if abs(amount - order.get('total_amount', 0)) > 0.01:
            return jsonify({
                'success': False,
                'message': 'भुक्तानी रकम मेल खाएन / Payment amount mismatch'
            }), 400
        
        # Initiate payment
        result = payment_manager.initiate_payment(
            gateway_name=gateway_name,
            amount=amount,
            order_number=order_number,
            customer_info=customer_info
        )
        
        # Log payment initiation
        log_payment_attempt(order_number, gateway_name, 'initiate', result)
        
        return jsonify(result)
        
    except ValueError as e:
        logger.error(f"Payment initiation validation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'अवैध डेटा / Invalid data',
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'भुक्तानी सुरु गर्न सकिएन / Failed to initiate payment',
            'error': str(e)
        }), 500

@payment_api.route('/verify', methods=['POST'])
def verify_payment():
    """
    Verify payment through specified gateway.
    
    Expected JSON payload varies by gateway:
    
    Khalti:
    {
        "gateway": "khalti",
        "pidx": "payment_index_from_khalti",
        "order_number": "ORD123456"
    }
    
    eSewa:
    {
        "gateway": "esewa",
        "oid": "order_id",
        "amt": "amount",
        "refId": "reference_id"
    }
    
    Returns:
        JSON response with verification result
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'JSON डेटा आवश्यक छ / JSON data required'
            }), 400
        
        data = request.get_json()
        
        # Validate gateway
        if 'gateway' not in data:
            return jsonify({
                'success': False,
                'message': 'गेटवे निर्दिष्ट गरिएको छैन / Gateway not specified'
            }), 400
        
        gateway_name = data['gateway'].lower()
        
        # Validate payment data
        if not payment_manager.validate_payment_data(gateway_name, data):
            return jsonify({
                'success': False,
                'message': 'अवैध भुक्तानी डेटा / Invalid payment data'
            }), 400
        
        # Verify payment
        result = payment_manager.verify_payment(gateway_name, data)
        
        # If verification successful, update order
        if result.get('verified'):
            order_number = result.get('order_number') or data.get('order_number') or data.get('oid')
            
            if order_number:
                update_result = update_order_payment_status(
                    order_number=order_number,
                    payment_status='paid',
                    transaction_id=result.get('transaction_id'),
                    gateway=gateway_name,
                    verification_data=result
                )
                
                if not update_result['success']:
                    logger.error(f"Failed to update order {order_number}: {update_result['message']}")
                    result['order_update_warning'] = update_result['message']
        
        # Log verification attempt
        log_payment_attempt(
            order_number=result.get('order_number', 'Unknown'),
            gateway=gateway_name,
            action='verify',
            result=result
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return jsonify({
            'success': False,
            'verified': False,
            'message': 'भुक्तानी प्रमाणीकरणमा समस्या / Payment verification failed',
            'error': str(e)
        }), 500

@payment_api.route('/status/<gateway_name>', methods=['GET'])
def get_gateway_status(gateway_name):
    """Get status of specific payment gateway."""
    try:
        status = payment_manager.get_gateway_status(gateway_name.lower())
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error fetching gateway status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'गेटवे स्थिति प्राप्त गर्न सकिएन / Failed to fetch gateway status',
            'error': str(e)
        }), 500

@payment_api.route('/status', methods=['GET'])
def get_all_gateway_status():
    """Get status of all payment gateways."""
    try:
        status = payment_manager.get_all_gateway_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error fetching all gateway status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'गेटवे स्थिति प्राप्त गर्न सकिएन / Failed to fetch gateway status',
            'error': str(e)
        }), 500

def update_order_payment_status(order_number: str, payment_status: str, 
                               transaction_id: str = None, gateway: str = None,
                               verification_data: dict = None) -> dict:
    """
    Update order payment status in database.
    
    Args:
        order_number: Order number to update
        payment_status: New payment status
        transaction_id: Transaction ID from gateway
        gateway: Payment gateway used
        verification_data: Full verification response
    
    Returns:
        Dict with update result
    """
    try:
        order = Order.find_by_order_number(order_number)
        if not order:
            return {
                'success': False,
                'message': f'Order {order_number} not found'
            }
        
        # Prepare update data
        update_data = {
            'payment_status': payment_status,
            'payment_updated_at': datetime.now()
        }
        
        if transaction_id:
            update_data['transaction_id'] = transaction_id
        
        if gateway:
            update_data['payment_gateway'] = gateway
        
        if verification_data:
            update_data['payment_verification'] = verification_data
        
        # Update order
        success = Order.update_order(order_number, update_data)
        
        if success:
            logger.info(f"Order {order_number} payment status updated to {payment_status}")
            return {
                'success': True,
                'message': f'Order {order_number} updated successfully'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to update order {order_number}'
            }
            
    except Exception as e:
        logger.error(f"Error updating order payment status: {str(e)}")
        return {
            'success': False,
            'message': f'Database update error: {str(e)}'
        }

def log_payment_attempt(order_number: str, gateway: str, action: str, result: dict):
    """
    Log payment attempt to file for debugging and audit.
    
    Args:
        order_number: Order number
        gateway: Payment gateway
        action: Action performed (initiate/verify)
        result: Result of the action
    """
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'order_number': order_number,
            'gateway': gateway,
            'action': action,
            'success': result.get('success', False),
            'verified': result.get('verified', None),
            'message': result.get('message', ''),
            'transaction_id': result.get('transaction_id'),
            'error': result.get('error')
        }
        
        # Ensure logs directory exists
        log_dir = os.path.join('instance', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Write to payment log file
        log_file = os.path.join(log_dir, 'payment_attempts.json')
        
        # Read existing logs
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Write back to file
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error logging payment attempt: {str(e)}")

# Error handlers
@payment_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'गलत अनुरोध / Bad request',
        'error': str(error)
    }), 400

@payment_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'फेला परेन / Not found',
        'error': str(error)
    }), 404

@payment_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'सर्भर त्रुटि / Internal server error',
        'error': str(error)
    }), 500