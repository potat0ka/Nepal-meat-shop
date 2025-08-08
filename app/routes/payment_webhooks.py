#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment Webhook Routes
Secure webhook handlers for payment gateway callbacks.
"""

from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app
from flask_login import current_user
from app.services.payment_service import payment_service
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoOrder
from app.models.order import Order
from app import db
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

payment_webhooks_bp = Blueprint('payment_webhooks', __name__, url_prefix='/payment')

@payment_webhooks_bp.route('/esewa/success')
def esewa_success():
    """Handle eSewa payment success callback."""
    try:
        # Get payment parameters from eSewa
        payment_data = {
            'oid': request.args.get('oid'),  # Order ID
            'refId': request.args.get('refId'),  # eSewa reference ID
            'amt': request.args.get('amt'),  # Amount
            'pid': request.args.get('pid')   # Product ID
        }
        
        logger.info(f"eSewa success callback received: {payment_data}")
        
        # Verify payment with eSewa
        verification_result = payment_service.verify_esewa_payment(payment_data)
        
        if verification_result.get('verified'):
            # Update order payment status
            order_number = verification_result.get('order_number')
            transaction_id = verification_result.get('transaction_id')
            
            success = update_order_payment_status(
                order_number, 
                'paid', 
                transaction_id,
                'esewa'
            )
            
            if success:
                # Log successful payment
                payment_service.log_payment_attempt(
                    order_number, 
                    'esewa', 
                    float(verification_result.get('amount', 0)),
                    'verified',
                    verification_result
                )
                
                flash('भुक्तानी सफल भयो! / Payment successful!', 'success')
                return redirect(url_for('orders.order_detail', order_id=get_order_id_by_number(order_number)))
            else:
                flash('भुक्तानी सफल भए पनि अर्डर अपडेट गर्न सकिएन / Payment successful but order update failed', 'warning')
        else:
            flash('भुक्तानी प्रमाणीकरण असफल / Payment verification failed', 'error')
            
    except Exception as e:
        logger.error(f"eSewa success handler error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
    
    return redirect(url_for('main.index'))

@payment_webhooks_bp.route('/esewa/failure')
def esewa_failure():
    """Handle eSewa payment failure callback."""
    try:
        order_id = request.args.get('pid')
        logger.info(f"eSewa payment failed for order: {order_id}")
        
        # Update order payment status to failed
        if order_id:
            update_order_payment_status(order_id, 'failed', None, 'esewa')
            
            # Log failed payment
            payment_service.log_payment_attempt(
                order_id, 
                'esewa', 
                0,
                'failed',
                {'reason': 'eSewa payment cancelled or failed'}
            )
        
        flash('भुक्तानी रद्द भयो / Payment cancelled', 'warning')
        
    except Exception as e:
        logger.error(f"eSewa failure handler error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
    
    return redirect(url_for('main.index'))

@payment_webhooks_bp.route('/khalti/success')
def khalti_success():
    """Handle Khalti payment success callback."""
    try:
        # Get payment parameters from Khalti
        payment_data = {
            'pidx': request.args.get('pidx'),
            'transaction_id': request.args.get('transaction_id'),
            'purchase_order_id': request.args.get('purchase_order_id'),
            'amount': request.args.get('amount')
        }
        
        logger.info(f"Khalti success callback received: {payment_data}")
        
        # Verify payment with Khalti
        verification_result = payment_service.verify_khalti_payment(payment_data)
        
        if verification_result.get('verified'):
            # Update order payment status
            order_number = verification_result.get('order_number')
            transaction_id = verification_result.get('transaction_id')
            
            success = update_order_payment_status(
                order_number, 
                'paid', 
                transaction_id,
                'khalti'
            )
            
            if success:
                # Log successful payment
                payment_service.log_payment_attempt(
                    order_number, 
                    'khalti', 
                    float(verification_result.get('amount', 0)),
                    'verified',
                    verification_result
                )
                
                flash('भुक्तानी सफल भयो! / Payment successful!', 'success')
                return redirect(url_for('orders.order_detail', order_id=get_order_id_by_number(order_number)))
            else:
                flash('भुक्तानी सफल भए पनि अर्डर अपडेट गर्न सकिएन / Payment successful but order update failed', 'warning')
        else:
            flash('भुक्तानी प्रमाणीकरण असफल / Payment verification failed', 'error')
            
    except Exception as e:
        logger.error(f"Khalti success handler error: {str(e)}")
        flash('भुक्तानी प्रक्रियामा समस्या / Payment processing error', 'error')
    
    return redirect(url_for('main.index'))

@payment_webhooks_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook for payment verification."""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('Stripe-Signature')
        
        logger.info("Stripe webhook received")
        
        # Verify webhook signature and process payment
        verification_result = payment_service.verify_stripe_webhook(payload, signature)
        
        if verification_result.get('verified'):
            # Extract order information from webhook data
            # In production, you would parse the webhook payload to get order details
            transaction_id = verification_result.get('transaction_id')
            amount = verification_result.get('amount')
            
            # For demo purposes, assume order number is in metadata
            # In production, you would include order number in Stripe metadata
            order_number = f"ORD-{transaction_id[-8:]}"  # Mock order number
            
            success = update_order_payment_status(
                order_number, 
                'paid', 
                transaction_id,
                'stripe'
            )
            
            if success:
                # Log successful payment
                payment_service.log_payment_attempt(
                    order_number, 
                    'stripe', 
                    amount,
                    'verified',
                    verification_result
                )
                
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"Failed to update order {order_number} after Stripe payment")
                return jsonify({'status': 'error', 'message': 'Order update failed'}), 500
        else:
            logger.error("Stripe webhook verification failed")
            return jsonify({'status': 'error', 'message': 'Verification failed'}), 400
            
    except Exception as e:
        logger.error(f"Stripe webhook handler error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Webhook processing failed'}), 500

@payment_webhooks_bp.route('/verify/<payment_method>', methods=['POST'])
def manual_payment_verification(payment_method):
    """Manual payment verification endpoint for admin use."""
    try:
        if not current_user.is_authenticated or not current_user.can_manage_orders():
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        order_number = data.get('order_number')
        transaction_id = data.get('transaction_id')
        
        if not order_number or not transaction_id:
            return jsonify({'error': 'Order number and transaction ID required'}), 400
        
        # Update order payment status
        success = update_order_payment_status(
            order_number, 
            'paid', 
            transaction_id,
            payment_method
        )
        
        if success:
            # Log manual verification
            payment_service.log_payment_attempt(
                order_number, 
                payment_method, 
                0,  # Amount not provided in manual verification
                'manually_verified',
                {
                    'verified_by': current_user.username,
                    'transaction_id': transaction_id
                }
            )
            
            return jsonify({'status': 'success', 'message': 'Payment verified successfully'})
        else:
            return jsonify({'error': 'Failed to update order'}), 500
            
    except Exception as e:
        logger.error(f"Manual verification error: {str(e)}")
        return jsonify({'error': 'Verification failed'}), 500

def update_order_payment_status(order_number: str, payment_status: str, 
                               transaction_id: str = None, payment_method: str = None) -> bool:
    """Update order payment status in both SQLite and MongoDB."""
    try:
        updated = False
        
        # Try MongoDB first
        if mongo_db.db is not None:
            try:
                result = mongo_db.db.orders.update_one(
                    {'order_number': order_number},
                    {
                        '$set': {
                            'payment_status': payment_status,
                            'transaction_id': transaction_id,
                            'payment_verified_at': datetime.utcnow() if payment_status == 'paid' else None
                        }
                    }
                )
                if result.modified_count > 0:
                    updated = True
                    logger.info(f"MongoDB order {order_number} payment status updated to {payment_status}")
            except Exception as e:
                logger.error(f"MongoDB update error: {str(e)}")
        
        # Try SQLite as fallback
        try:
            order = Order.query.filter_by(order_number=order_number).first()
            if order:
                order.payment_status = payment_status
                if transaction_id:
                    order.transaction_id = transaction_id
                db.session.commit()
                updated = True
                logger.info(f"SQLite order {order_number} payment status updated to {payment_status}")
        except Exception as e:
            logger.error(f"SQLite update error: {str(e)}")
            db.session.rollback()
        
        return updated
        
    except Exception as e:
        logger.error(f"Order update error: {str(e)}")
        return False

def get_order_id_by_number(order_number: str) -> str:
    """Get order ID by order number for redirect purposes."""
    try:
        # Try MongoDB first
        if mongo_db.db is not None:
            order_data = mongo_db.db.orders.find_one({'order_number': order_number})
            if order_data:
                return str(order_data['_id'])
        
        # Try SQLite as fallback
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            return str(order.id)
            
    except Exception as e:
        logger.error(f"Error getting order ID: {str(e)}")
    
    return None