#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Callback Routes
Handle payment gateway callbacks and redirects
"""

import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash
from urllib.parse import urlencode

from app.services.gateways import payment_manager
from app.models.mongo_models import MongoOrder as Order

logger = logging.getLogger(__name__)

# Create blueprint
payment_callbacks = Blueprint('payment_callbacks', __name__, url_prefix='/payment')

@payment_callbacks.route('/khalti/success')
def khalti_success():
    """
    Handle Khalti payment success callback.
    
    Expected parameters:
    - pidx: Payment index from Khalti
    - transaction_id: Transaction ID
    - tidx: Transaction index
    - amount: Payment amount
    - mobile: Customer mobile
    - purchase_order_id: Order number
    - purchase_order_name: Order name
    """
    try:
        # Get callback parameters
        pidx = request.args.get('pidx')
        transaction_id = request.args.get('transaction_id')
        tidx = request.args.get('tidx')
        amount = request.args.get('amount')
        mobile = request.args.get('mobile')
        purchase_order_id = request.args.get('purchase_order_id')
        purchase_order_name = request.args.get('purchase_order_name')
        
        logger.info(f"Khalti success callback: pidx={pidx}, order={purchase_order_id}")
        
        if not pidx or not purchase_order_id:
            flash('भुक्तानी जानकारी अपूर्ण छ / Payment information incomplete', 'error')
            return redirect(url_for('orders.order_status', order_number=purchase_order_id or 'unknown'))
        
        # Verify payment with Khalti
        verification_data = {
            'pidx': pidx,
            'order_number': purchase_order_id
        }
        
        result = payment_manager.verify_payment('khalti', verification_data)
        
        if result.get('verified'):
            flash('Khalti भुक्तानी सफल भयो! / Khalti payment successful!', 'success')
            return redirect(url_for('orders.order_success', order_number=purchase_order_id))
        else:
            flash('Khalti भुक्तानी प्रमाणीकरण असफल / Khalti payment verification failed', 'error')
            return redirect(url_for('orders.order_status', order_number=purchase_order_id))
            
    except Exception as e:
        logger.error(f"Khalti success callback error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/khalti/failure')
def khalti_failure():
    """Handle Khalti payment failure callback."""
    try:
        # Get callback parameters
        pidx = request.args.get('pidx')
        purchase_order_id = request.args.get('purchase_order_id')
        
        logger.info(f"Khalti failure callback: pidx={pidx}, order={purchase_order_id}")
        
        flash('Khalti भुक्तानी रद्द गरियो / Khalti payment cancelled', 'warning')
        
        if purchase_order_id:
            return redirect(url_for('orders.order_status', order_number=purchase_order_id))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"Khalti failure callback error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/esewa/success')
def esewa_success():
    """
    Handle eSewa payment success callback.
    
    Expected parameters:
    - oid: Order ID
    - amt: Amount
    - refId: Reference ID from eSewa
    """
    try:
        # Get callback parameters
        oid = request.args.get('oid')
        amt = request.args.get('amt')
        ref_id = request.args.get('refId')
        
        logger.info(f"eSewa success callback: oid={oid}, amt={amt}, refId={ref_id}")
        
        if not all([oid, amt, ref_id]):
            flash('eSewa भुक्तानी जानकारी अपूर्ण छ / eSewa payment information incomplete', 'error')
            return redirect(url_for('orders.order_status', order_number=oid or 'unknown'))
        
        # Verify payment with eSewa
        verification_data = {
            'oid': oid,
            'amt': amt,
            'refId': ref_id
        }
        
        result = payment_manager.verify_payment('esewa', verification_data)
        
        if result.get('verified'):
            flash('eSewa भुक्तानी सफल भयो! / eSewa payment successful!', 'success')
            return redirect(url_for('orders.order_success', order_number=oid))
        else:
            flash('eSewa भुक्तानी प्रमाणीकरण असफल / eSewa payment verification failed', 'error')
            return redirect(url_for('orders.order_status', order_number=oid))
            
    except Exception as e:
        logger.error(f"eSewa success callback error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/esewa/failure')
def esewa_failure():
    """Handle eSewa payment failure callback."""
    try:
        # Get callback parameters
        oid = request.args.get('oid')
        
        logger.info(f"eSewa failure callback: oid={oid}")
        
        flash('eSewa भुक्तानी रद्द गरियो / eSewa payment cancelled', 'warning')
        
        if oid:
            return redirect(url_for('orders.order_status', order_number=oid))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"eSewa failure callback error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/status/<order_number>')
def payment_status(order_number):
    """
    Display payment status page for an order.
    
    Args:
        order_number: Order number to check status
    """
    try:
        # Find order
        order = Order.find_by_order_number(order_number)
        
        if not order:
            flash('अर्डर फेला परेन / Order not found', 'error')
            return redirect(url_for('main.index'))
        
        # Get payment gateway status if available
        gateway_status = None
        if order.get('payment_gateway'):
            gateway_status = payment_manager.get_gateway_status(order['payment_gateway'])
        
        return render_template('orders/payment_status.html', 
                             order=order, 
                             gateway_status=gateway_status)
        
    except Exception as e:
        logger.error(f"Payment status page error: {str(e)}")
        flash('स्थिति जाँच गर्न सकिएन / Unable to check status', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/retry/<order_number>')
def retry_payment(order_number):
    """
    Retry payment for a failed or pending order.
    
    Args:
        order_number: Order number to retry payment
    """
    try:
        # Find order
        order = Order.find_by_order_number(order_number)
        
        if not order:
            flash('अर्डर फेला परेन / Order not found', 'error')
            return redirect(url_for('main.index'))
        
        # Check if order can be retried
        if order.get('payment_status') == 'paid':
            flash('यो अर्डर पहिले नै भुक्तानी भइसकेको छ / Order already paid', 'info')
            return redirect(url_for('orders.order_success', order_number=order_number))
        
        # Redirect to checkout with order number
        return redirect(url_for('orders.checkout', order_number=order_number))
        
    except Exception as e:
        logger.error(f"Payment retry error: {str(e)}")
        flash('भुक्तानी पुनः प्रयास गर्न सकिएन / Unable to retry payment', 'error')
        return redirect(url_for('main.index'))

@payment_callbacks.route('/webhook/<gateway_name>', methods=['POST'])
def payment_webhook(gateway_name):
    """
    Handle payment gateway webhooks for real-time notifications.
    
    Args:
        gateway_name: Name of the payment gateway
    """
    try:
        # Get webhook data
        webhook_data = request.get_json() or request.form.to_dict()
        
        logger.info(f"Received {gateway_name} webhook: {webhook_data}")
        
        # Validate gateway
        if not payment_manager.is_gateway_available(gateway_name.lower()):
            logger.warning(f"Webhook received for unavailable gateway: {gateway_name}")
            return {'status': 'error', 'message': 'Gateway not available'}, 400
        
        # Process webhook based on gateway
        if gateway_name.lower() == 'khalti':
            return process_khalti_webhook(webhook_data)
        elif gateway_name.lower() == 'esewa':
            return process_esewa_webhook(webhook_data)
        else:
            logger.warning(f"Webhook handler not implemented for: {gateway_name}")
            return {'status': 'error', 'message': 'Webhook handler not implemented'}, 501
            
    except Exception as e:
        logger.error(f"Webhook processing error for {gateway_name}: {str(e)}")
        return {'status': 'error', 'message': 'Webhook processing failed'}, 500

def process_khalti_webhook(webhook_data):
    """Process Khalti webhook notification."""
    try:
        # Khalti webhook processing logic
        # This would typically include signature verification
        # and payment status updates
        
        logger.info("Processing Khalti webhook")
        return {'status': 'success', 'message': 'Webhook processed'}
        
    except Exception as e:
        logger.error(f"Khalti webhook processing error: {str(e)}")
        return {'status': 'error', 'message': 'Webhook processing failed'}, 500

def process_esewa_webhook(webhook_data):
    """Process eSewa webhook notification."""
    try:
        # eSewa webhook processing logic
        # This would typically include signature verification
        # and payment status updates
        
        logger.info("Processing eSewa webhook")
        return {'status': 'success', 'message': 'Webhook processed'}
        
    except Exception as e:
        logger.error(f"eSewa webhook processing error: {str(e)}")
        return {'status': 'error', 'message': 'Webhook processing failed'}, 500