
import uuid
from datetime import datetime
from flask import flash

def process_payment(payment_method, amount, order_number):
    """
    Simulate payment processing for different Nepali payment methods.
    In production, this would integrate with actual payment gateways.
    """
    
    # Generate transaction ID
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
    
    # Simulate payment processing
    if payment_method == 'cod':
        return {
            'success': True,
            'transaction_id': None,
            'message': 'Cash on Delivery order placed successfully',
            'payment_status': 'pending'
        }
    
    elif payment_method == 'esewa':
        # Simulate eSewa payment
        return simulate_esewa_payment(amount, transaction_id, order_number)
    
    elif payment_method == 'khalti':
        # Simulate Khalti payment
        return simulate_khalti_payment(amount, transaction_id, order_number)
    
    elif payment_method == 'phonepay':
        # Simulate PhonePay payment
        return simulate_phonepay_payment(amount, transaction_id, order_number)
    
    elif payment_method == 'mobile_banking':
        # Simulate Mobile Banking payment
        return simulate_mobile_banking_payment(amount, transaction_id, order_number)
    
    elif payment_method == 'bank_transfer':
        # Simulate Bank Transfer
        return simulate_bank_transfer_payment(amount, transaction_id, order_number)
    
    else:
        return {
            'success': False,
            'transaction_id': None,
            'message': 'Invalid payment method',
            'payment_status': 'failed'
        }

def simulate_esewa_payment(amount, transaction_id, order_number):
    """Simulate eSewa payment processing."""
    # In real implementation, this would redirect to eSewa gateway
    # For simulation, we'll assume 95% success rate
    import random
    
    if random.random() < 0.95:  # 95% success rate
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'eSewa payment successful. Transaction ID: {transaction_id}',
            'payment_status': 'paid',
            'gateway_response': {
                'oid': order_number,
                'amt': amount,
                'refId': transaction_id,
                'pid': 'esewa_' + transaction_id
            }
        }
    else:
        return {
            'success': False,
            'transaction_id': transaction_id,
            'message': 'eSewa payment failed. Please try again.',
            'payment_status': 'failed'
        }

def simulate_khalti_payment(amount, transaction_id, order_number):
    """Simulate Khalti payment processing."""
    import random
    
    if random.random() < 0.93:  # 93% success rate
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'Khalti payment successful. Transaction ID: {transaction_id}',
            'payment_status': 'paid',
            'gateway_response': {
                'pidx': transaction_id,
                'amount': amount * 100,  # Khalti uses paisa
                'purchase_order_id': order_number,
                'purchase_order_name': 'Nepal Meat Shop Order'
            }
        }
    else:
        return {
            'success': False,
            'transaction_id': transaction_id,
            'message': 'Khalti payment failed. Please try again.',
            'payment_status': 'failed'
        }

def simulate_phonepay_payment(amount, transaction_id, order_number):
    """Simulate PhonePay payment processing."""
    import random
    
    if random.random() < 0.90:  # 90% success rate
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'PhonePay payment successful. Transaction ID: {transaction_id}',
            'payment_status': 'paid',
            'gateway_response': {
                'merchantTransactionId': transaction_id,
                'amount': amount,
                'currency': 'NPR',
                'orderId': order_number
            }
        }
    else:
        return {
            'success': False,
            'transaction_id': transaction_id,
            'message': 'PhonePay payment failed. Please try again.',
            'payment_status': 'failed'
        }

def simulate_mobile_banking_payment(amount, transaction_id, order_number):
    """Simulate Mobile Banking payment processing."""
    import random
    
    if random.random() < 0.88:  # 88% success rate
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'Mobile Banking payment successful. Transaction ID: {transaction_id}',
            'payment_status': 'paid',
            'gateway_response': {
                'bankTransactionId': transaction_id,
                'amount': amount,
                'currency': 'NPR',
                'referenceNumber': order_number,
                'bankName': 'Nepal Bank Ltd'
            }
        }
    else:
        return {
            'success': False,
            'transaction_id': transaction_id,
            'message': 'Mobile Banking payment failed. Please try again.',
            'payment_status': 'failed'
        }

def simulate_bank_transfer_payment(amount, transaction_id, order_number):
    """Simulate Bank Transfer payment processing."""
    # Bank transfers are usually manual verification
    return {
        'success': True,
        'transaction_id': transaction_id,
        'message': f'Bank transfer initiated. Please complete the transfer and provide reference: {transaction_id}',
        'payment_status': 'pending',
        'gateway_response': {
            'transferReference': transaction_id,
            'amount': amount,
            'accountDetails': {
                'bankName': 'Nepal Meat Shop Account',
                'accountNumber': '1234567890',
                'accountName': 'Nepal Meat Shop Pvt Ltd'
            }
        }
    }

def get_payment_instructions(payment_method):
    """Get payment method specific instructions."""
    
    instructions = {
        'cod': {
            'title': 'Cash on Delivery',
            'instruction': 'Pay cash when your order is delivered to your address.',
            'icon': 'fas fa-money-bill-wave'
        },
        'esewa': {
            'title': 'eSewa Digital Wallet',
            'instruction': 'You will be redirected to eSewa to complete the payment.',
            'icon': 'fas fa-mobile-alt'
        },
        'khalti': {
            'title': 'Khalti Digital Wallet',
            'instruction': 'You will be redirected to Khalti to complete the payment.',
            'icon': 'fas fa-mobile-alt'
        },
        'phonepay': {
            'title': 'PhonePay',
            'instruction': 'You will be redirected to PhonePay to complete the payment.',
            'icon': 'fas fa-mobile-alt'
        },
        'mobile_banking': {
            'title': 'Mobile Banking',
            'instruction': 'You will be redirected to your bank\'s mobile banking portal.',
            'icon': 'fas fa-university'
        },
        'bank_transfer': {
            'title': 'Bank Transfer',
            'instruction': 'Transfer the amount to our bank account and provide the reference number.',
            'icon': 'fas fa-university'
        }
    }
    
    return instructions.get(payment_method, {
        'title': 'Unknown Payment Method',
        'instruction': 'Please select a valid payment method.',
        'icon': 'fas fa-question-circle'
    })
