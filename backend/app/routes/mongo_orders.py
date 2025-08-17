#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Orders Routes
Order management, cart, and checkout routes for MongoDB.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoOrder
from app.forms.order import CheckoutForm
from datetime import datetime
import uuid

# Create orders blueprint
mongo_orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@mongo_orders_bp.route('/cart')
def cart():
    """
    Shopping cart page.
    """
    cart_items = session.get('cart', {})
    cart_products = []
    total_amount = 0
    
    for product_id, quantity in cart_items.items():
        product = mongo_db.find_product_by_id(product_id)
        if product and product.is_available:
            item_total = product.price * quantity
            cart_products.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total_amount += item_total
    
    return render_template('cart/cart.html',
                         cart_items=cart_products,
                         total=total_amount)

@mongo_orders_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """
    Add product to cart via AJAX or form submission.
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = float(data.get('quantity', 1))
        else:
            # Handle form data
            product_id = request.form.get('product_id')
            quantity = float(request.form.get('quantity', 1))
        
        # Validate product
        product = mongo_db.find_product_by_id(product_id)
        if not product or not product.is_available:
            if request.is_json:
                return jsonify({'error': 'Product not found or unavailable'}), 404
            else:
                flash('Product not found or unavailable', 'error')
                return redirect(url_for('products.detail', product_id=product_id))
        
        # Check stock
        if quantity > product.stock_quantity:
            if request.is_json:
                return jsonify({'error': 'Insufficient stock'}), 400
            else:
                flash(f'Only {product.stock_quantity} kg available in stock', 'error')
                return redirect(url_for('products.detail', product_id=product_id))
        
        # Initialize cart if not exists
        if 'cart' not in session:
            session['cart'] = {}
        
        # Add to cart
        cart = session['cart']
        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity
        
        # Check total quantity doesn't exceed stock
        if cart[product_id] > product.stock_quantity:
            cart[product_id] = product.stock_quantity
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': f'Added maximum available quantity ({product.stock_quantity}) to cart',
                    'cart_count': sum(cart.values())
                })
            else:
                flash(f'Added maximum available quantity ({product.stock_quantity} kg) to cart', 'warning')
                return redirect(url_for('orders.cart'))
        
        session['cart'] = cart
        session.modified = True
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Product added to cart',
                'cart_count': sum(cart.values())
            })
        else:
            flash(f'Added {quantity} kg of {product.name} to cart', 'success')
            return redirect(url_for('orders.cart'))
    
    except Exception as e:
        if request.is_json:
            return jsonify({'error': 'Failed to add product to cart'}), 500
        else:
            flash('Failed to add product to cart', 'error')
            return redirect(url_for('products.detail', product_id=product_id))

@mongo_orders_bp.route('/update-cart', methods=['POST'])
def update_cart():
    """
    Update cart item quantity.
    Handles both JSON (AJAX) and form POST requests.
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 0))
        else:
            # Handle form data
            product_id = request.form.get('product_id')
            quantity = float(request.form.get('quantity', 0))
        
        if not product_id:
            if request.is_json:
                return jsonify({'error': 'Product ID is required'}), 400
            else:
                flash('Product ID is required', 'error')
                return redirect(url_for('orders.cart'))
        
        if 'cart' not in session:
            if request.is_json:
                return jsonify({'error': 'Cart is empty'}), 400
            else:
                flash('Cart is empty', 'warning')
                return redirect(url_for('orders.cart'))
        
        cart = session['cart']
        
        if quantity <= 0:
            # Remove item from cart
            if product_id in cart:
                del cart[product_id]
                if not request.is_json:
                    flash('✅ कार्टबाट हटाइयो / Item removed from cart', 'success')
        else:
            # Update quantity
            product = mongo_db.find_product_by_id(product_id)
            if not product:
                if request.is_json:
                    return jsonify({'error': 'Product not found'}), 404
                else:
                    flash('❌ उत्पादन फेला परेन / Product not found', 'error')
                    return redirect(url_for('orders.cart'))
            
            if quantity > product.stock_quantity:
                quantity = product.stock_quantity
                if not request.is_json:
                    flash(f'⚠️ केवल {quantity} केजी स्टकमा छ / Only {quantity} kg in stock', 'warning')
            
            cart[product_id] = quantity
            if not request.is_json:
                flash(f'✅ मात्रा अपडेट भयो / Quantity updated: {quantity} kg', 'success')
        
        session['cart'] = cart
        session.modified = True
        
        # Calculate new totals
        total_amount = 0
        for pid, qty in cart.items():
            product = mongo_db.find_product_by_id(pid)
            if product:
                total_amount += product.price * qty
        
        if request.is_json:
            return jsonify({
                'success': True,
                'cart_count': sum(cart.values()),
                'total_amount': total_amount
            })
        else:
            return redirect(url_for('orders.cart'))
    
    except Exception as e:
        if request.is_json:
            return jsonify({'error': 'Failed to update cart'}), 500
        else:
            flash('❌ कार्ट अपडेट गर्न सकिएन / Failed to update cart', 'error')
            return redirect(url_for('orders.cart'))

@mongo_orders_bp.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    """
    Remove product from cart.
    Handles both JSON (AJAX) and form POST requests.
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            product_id = data.get('product_id')
        else:
            # Handle form data
            product_id = request.form.get('product_id')
        
        if not product_id:
            if request.is_json:
                return jsonify({'error': 'Product ID is required'}), 400
            else:
                flash('Product ID is required', 'error')
                return redirect(url_for('orders.cart'))
        
        if 'cart' not in session:
            if request.is_json:
                return jsonify({'error': 'Cart is empty'}), 400
            else:
                flash('Cart is empty', 'warning')
                return redirect(url_for('orders.cart'))
        
        cart = session['cart']
        product_name = None
        
        # Get product name for flash message
        if product_id in cart:
            try:
                product = mongo_db.find_product_by_id(product_id)
                if product:
                    product_name = product.name
            except:
                pass
            
            del cart[product_id]
        
        session['cart'] = cart
        session.modified = True
        
        if request.is_json:
            return jsonify({
                'success': True,
                'cart_count': sum(cart.values())
            })
        else:
            if product_name:
                flash(f'✅ कार्टबाट हटाइयो / Removed from cart: {product_name}', 'success')
            else:
                flash('✅ कार्टबाट हटाइयो / Item removed from cart', 'success')
            return redirect(url_for('orders.cart'))
    
    except Exception as e:
        if request.is_json:
            return jsonify({'error': 'Failed to remove product from cart'}), 500
        else:
            flash('❌ कार्टबाट हटाउन सकिएन / Failed to remove item from cart', 'error')
            return redirect(url_for('orders.cart'))

@mongo_orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Checkout page for placing orders.
    """
    cart_items = session.get('cart', {})
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products.list'))
    
    cart_products = []
    total_amount = 0
    
    for product_id, quantity in cart_items.items():
        product = mongo_db.find_product_by_id(product_id)
        if product and product.is_available:
            item_total = product.price * quantity
            cart_products.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
            total_amount += item_total
    
    # Create checkout form
    form = CheckoutForm()
    
    # Handle POST request (form submission)
    if form.validate_on_submit():
        try:
            # Prepare order items and validate stock
            order_items = []
            final_total = 0
            
            for product_id, quantity in cart_items.items():
                product = mongo_db.find_product_by_id(product_id)
                if not product or not product.is_available:
                    flash(f'Product {product_id} is no longer available', 'error')
                    return redirect(url_for('orders.cart'))
                
                if quantity > product.stock_quantity:
                    flash(f'Insufficient stock for {product.name}. Only {product.stock_quantity} available.', 'error')
                    return redirect(url_for('orders.cart'))
                
                item_total = product.price * quantity
                order_items.append({
                    'product_id': str(product._id),
                    'product_name': product.name,
                    'quantity': quantity,
                    'unit_price': product.price,
                    'total_price': item_total
                })
                final_total += item_total
            
            # Set payment status based on method - all payments start as pending
            from app.services.payment_service import payment_service
            from app.services.gateways import payment_manager
            
            # Generate order number and transaction ID for tracking
            order_number = f'ORD-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:8].upper()}'
            transaction_id = payment_service._generate_transaction_id()
            
            payment_method = form.payment_method.data
            if payment_method == 'cod':
                payment_status = 'pending'
            else:
                # Digital payments remain pending until gateway confirmation
                payment_status = 'pending'
            
            # Log payment attempt using new payment manager
            try:
                payment_manager.log_payment_attempt(
                    order_number,
                    payment_method,
                    float(final_total),
                    'initiated',
                    {'transaction_id': transaction_id}
                )
            except Exception as e:
                print(f"Failed to log payment attempt: {e}")
                # Fallback to old payment service
                payment_service.log_payment_attempt(
                    order_number,
                    payment_method,
                    float(final_total),
                    'initiated',
                    {'transaction_id': transaction_id}
                )

            # Create order
            order_data = {
                'order_number': order_number,
                'user_id': str(current_user._id),
                'items': order_items,
                'total_amount': final_total,
                'delivery_address': form.delivery_address.data,
                'delivery_latitude': form.delivery_latitude.data if form.delivery_latitude.data else None,
                'delivery_longitude': form.delivery_longitude.data if form.delivery_longitude.data else None,
                'delivery_formatted_address': form.delivery_formatted_address.data if form.delivery_formatted_address.data else None,
                'phone_number': form.delivery_phone.data,
                'payment_method': payment_method,
                'special_instructions': form.special_instructions.data,
                'status': 'pending',
                'order_date': datetime.utcnow(),
                'estimated_delivery': None,
                'payment_status': payment_status,
                'transaction_id': transaction_id
            }
            
            # Save order to database
            order = MongoOrder(order_data)
            saved_order = mongo_db.save_order(order)
            
            if saved_order:
                # Update product stock quantities
                for item in order_items:
                    product = mongo_db.find_product_by_id(item['product_id'])
                    if product:
                        new_stock = product.stock_quantity - item['quantity']
                        mongo_db.db.products.update_one(
                            {'_id': product._id},
                            {'$set': {'stock_quantity': max(0, new_stock)}}
                        )
                
                # Clear cart
                session.pop('cart', None)
                session.modified = True
                
                # Check if this is an AJAX request
                if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                    # Return JSON response for AJAX requests
                    return jsonify({
                        'success': True,
                        'order_id': str(saved_order._id),
                        'order_number': order_number,
                        'message': 'Order placed successfully!'
                    })
                else:
                    # Success message based on payment method
                    if payment_method == 'cod':
                        flash('अर्डर सफल भयो! घरमा पैसा तिर्नुहोस् / Order placed successfully! Pay on delivery.', 'success')
                    else:
                        flash(f'अर्डर सफल भयो! भुक्तानी प्रमाणीकरणको लागि पर्खनुहोस् / Order placed! Awaiting payment verification via {payment_method.upper()}.', 'info')
                    
                    return redirect(url_for('orders.order_detail', order_id=str(saved_order._id)))
            else:
                flash('Failed to place order. Please try again.', 'error')
                
        except Exception as e:
            print(f"Order processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Error processing order. Please try again.', 'error')
    
    # Fetch QR codes for payment methods
    qr_codes = {}
    try:
        if mongo_db.db is not None:
            qr_code_docs = mongo_db.db.qr_codes.find({})
            for qr_doc in qr_code_docs:
                qr_codes[qr_doc['payment_method']] = {
                    'image_filename': qr_doc['qr_image'],
                    'description': qr_doc.get('description', ''),
                    'display_name': qr_doc.get('display_name', qr_doc['payment_method'])
                }
        else:
            # Fallback QR code data when MongoDB is not available
            print("MongoDB not available, using fallback QR code data")
            qr_codes = {
                'bank': {
                    'image_filename': 'qr_codes/bank_transfer_qr_code.svg',
                    'description': 'Bank Transfer QR Code for payments',
                    'display_name': 'Bank Transfer'
                },
                'esewa': {
                    'image_filename': 'qr_codes/esewa_qr_code.svg',
                    'description': 'Pay using eSewa digital wallet',
                    'display_name': 'eSewa'
                },
                'khalti': {
                    'image_filename': 'qr_codes/khalti_qr_code.svg',
                    'description': 'Pay using Khalti digital wallet',
                    'display_name': 'Khalti'
                },
                'ime_pay': {
                    'image_filename': 'qr_codes/ime_pay_qr_code.svg',
                    'description': 'Pay using IME Pay digital wallet',
                    'display_name': 'IME Pay'
                },
                'fonepay': {
                    'image_filename': 'qr_codes/fone_pay_qr_code.svg',
                    'description': 'Pay using FonePay digital wallet',
                    'display_name': 'FonePay'
                },
                'prabhupay': {
                    'image_filename': 'qr_codes/prabhu_pay_qr_code.svg',
                    'description': 'Pay using PrabhuPay digital wallet',
                    'display_name': 'PrabhuPay'
                },
                'cellpay': {
                    'image_filename': 'qr_codes/cell_pay_qr_code.svg',
                    'description': 'Pay using CellPay digital wallet',
                    'display_name': 'CellPay'
                }
            }
    except Exception as e:
        print(f"Error fetching QR codes: {str(e)}")
        # Fallback QR code data in case of any error
        qr_codes = {
            'bank': {
                'image_filename': 'qr_codes/bank_transfer_qr_code.svg',
                'description': 'Bank Transfer QR Code for payments',
                'display_name': 'Bank Transfer'
            },
            'esewa': {
                'image_filename': 'qr_codes/esewa_qr_code.svg',
                'description': 'Pay using eSewa digital wallet',
                'display_name': 'eSewa'
            },
            'khalti': {
                'image_filename': 'qr_codes/khalti_qr_code.svg',
                'description': 'Pay using Khalti digital wallet',
                'display_name': 'Khalti'
            },
            'ime_pay': {
                'image_filename': 'qr_codes/ime_pay_qr_code.svg',
                'description': 'Pay using IME Pay digital wallet',
                'display_name': 'IME Pay'
            },
            'fonepay': {
                'image_filename': 'qr_codes/fone_pay_qr_code.svg',
                'description': 'Pay using FonePay digital wallet',
                'display_name': 'FonePay'
            },
            'prabhupay': {
                'image_filename': 'qr_codes/prabhu_pay_qr_code.svg',
                'description': 'Pay using PrabhuPay digital wallet',
                'display_name': 'PrabhuPay'
            },
            'cellpay': {
                'image_filename': 'qr_codes/cell_pay_qr_code.svg',
                'description': 'Pay using CellPay digital wallet',
                'display_name': 'CellPay'
            }
        }
    
    return render_template('orders/checkout.html',
                         form=form,
                         cart_items=cart_products,
                         total=total_amount,
                         user=current_user,
                         qr_codes=qr_codes)

@mongo_orders_bp.route('/place-order', methods=['POST'])
@login_required
def place_order():
    """
    Place a new order.
    """
    try:
        cart_items = session.get('cart', {})
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Get form data
        delivery_address = request.form.get('delivery_address', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        special_instructions = request.form.get('special_instructions', '').strip()
        
        if not delivery_address or not phone_number:
            return jsonify({'error': 'Delivery address and phone number are required'}), 400
        
        # Prepare order items and calculate total
        order_items = []
        total_amount = 0
        
        for product_id, quantity in cart_items.items():
            product = mongo_db.find_product_by_id(product_id)
            if not product or not product.is_available:
                return jsonify({'error': f'Product {product_id} is no longer available'}), 400
            
            if quantity > product.stock_quantity:
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
            
            item_total = product.price * quantity
            order_items.append({
                'product_id': str(product._id),
                'product_name': product.name,
                'quantity': quantity,
                'unit_price': product.price,
                'total_price': item_total
            })
            total_amount += item_total
        
        # Create order
        order_data = {
            'order_number': f'ORD-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:8].upper()}',
            'user_id': str(current_user._id),
            'items': order_items,
            'total_amount': total_amount,
            'delivery_address': delivery_address,
            'phone_number': phone_number,
            'special_instructions': special_instructions,
            'status': 'pending',
            'order_date': datetime.utcnow(),
            'estimated_delivery': None,
            'payment_status': 'pending'
        }
        
        # Save order to database
        order = MongoOrder(order_data)
        saved_order = mongo_db.save_order(order)
        
        if saved_order:
            # Update product stock quantities
            for item in order_items:
                product = mongo_db.find_product_by_id(item['product_id'])
                if product:
                    new_stock = product.stock_quantity - item['quantity']
                    mongo_db.db.products.update_one(
                        {'_id': product._id},
                        {'$set': {'stock_quantity': max(0, new_stock)}}
                    )
            
            # Clear cart
            session.pop('cart', None)
            session.modified = True
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('orders.order_detail', order_id=str(saved_order._id)))
        else:
            return jsonify({'error': 'Failed to place order'}), 500
    
    except Exception as e:
        return jsonify({'error': 'Failed to place order'}), 500

@mongo_orders_bp.route('/')
@login_required
def my_orders():
    """
    User's order history.
    """
    orders = mongo_db.get_user_orders(str(current_user._id))
    return render_template('orders/my_orders.html', orders=orders)

@mongo_orders_bp.route('/<order_id>')
@login_required
def order_detail(order_id):
    """
    Order detail page.
    """
    order = mongo_db.find_order_by_id(order_id)
    
    if not order or order.user_id != str(current_user._id):
        flash('Order not found', 'error')
        return redirect(url_for('orders.my_orders'))
    
    return render_template('orders/detail.html', order=order)

@mongo_orders_bp.route('/api/cart-count')
def api_cart_count():
    """
    API endpoint to get cart item count.
    """
    cart_items = session.get('cart', {})
    return jsonify({'count': sum(cart_items.values())})

@mongo_orders_bp.route('/clear-cart', methods=['POST'])
def clear_cart():
    """
    Clear all items from cart.
    """
    session.pop('cart', None)
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Cart cleared',
        'cart_count': 0
    })