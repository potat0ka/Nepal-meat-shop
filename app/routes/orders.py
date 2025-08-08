#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Order & Cart Routes
Shopping cart, checkout, order management, and payment processing.
"""

import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Order, OrderItem, CartItem, DeliveryArea, Invoice
from app.forms import CartForm, UpdateCartForm, RemoveCartForm, CheckoutForm
from app.utils import (
    generate_order_number, 
    generate_invoice_number,
    calculate_delivery_charge,
    format_currency,
    validate_quantity
)

# Create orders blueprint
orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/cart')
@login_required
def cart():
    """
    Display shopping cart contents.
    """
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0

    for product_id_str, item in cart.items():
        # Get fresh product data to ensure current prices and availability
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            item_total = item['quantity'] * product.price
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total': item_total
            })
            subtotal += item_total
        else:
            # Remove inactive products from cart
            cart.pop(product_id_str, None)
            session['cart'] = cart
            session.modified = True

    # Calculate delivery charge
    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge

    return render_template('cart/cart.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_charge=delivery_charge,
                         total=total)

@orders_bp.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    """
    Add item to shopping cart.
    """
    # Get form data
    product_id_str = request.form.get('product_id', '').strip()
    quantity_str = request.form.get('quantity', '').strip()
    
    # Validate input
    if not product_id_str or not quantity_str:
        flash('❌ उत्पादन र मात्रा आवश्यक छ / Product and quantity required', 'error')
        return redirect(url_for('products.list'))

    try:
        product_id = int(product_id_str)
        quantity = float(quantity_str)
    except (ValueError, TypeError):
        flash('❌ गलत डेटा / Invalid data provided', 'error')
        return redirect(url_for('products.list'))

    # Get product
    product = Product.query.get_or_404(product_id)

    # Validate quantity
    quantity_validation = validate_quantity(quantity, min_qty=0.5, max_qty=product.stock_kg)
    if not quantity_validation['valid']:
        flash(f'❌ {quantity_validation["error"]}', 'error')
        return redirect(url_for('products.detail', product_id=product_id))

    # Check stock availability
    if quantity > product.stock_kg:
        flash(f'❌ केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
        return redirect(url_for('products.detail', product_id=product_id))

    # Initialize cart in session
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    product_id_str = str(product_id)

    # Add or update cart item
    if product_id_str in cart:
        # Update existing item
        new_quantity = cart[product_id_str]['quantity'] + quantity
        if new_quantity > product.stock_kg:
            flash(f'❌ कुल मात्रा {product.stock_kg} केजीभन्दा बढी हुन सक्दैन / Total quantity cannot exceed {product.stock_kg} kg', 'error')
            return redirect(url_for('products.detail', product_id=product_id))

        cart[product_id_str]['quantity'] = new_quantity
        flash(f'✅ कार्टमा मात्रा अपडेट भयो / Cart updated: {new_quantity} kg', 'success')
    else:
        # Add new item
        cart[product_id_str] = {
            'product_id': product_id,
            'name': product.name,
            'name_nepali': product.name_nepali,
            'price': product.price,
            'quantity': quantity,
            'image_url': product.image_url
        }
        flash(f'✅ कार्टमा थपियो / Added to cart: {product.name} ({quantity} kg)', 'success')

    # Save cart to session
    session['cart'] = cart
    session.modified = True

    return redirect(url_for('orders.cart'))

@orders_bp.route('/update-cart', methods=['POST'])
@login_required
def update_cart():
    """
    Update cart item quantity.
    """
    form = UpdateCartForm()
    if form.validate_on_submit():
        product_id = int(form.product_id.data)
        quantity = float(form.quantity.data)

        product = Product.query.get_or_404(product_id)

        # Validate quantity
        quantity_validation = validate_quantity(quantity, min_qty=0.5, max_qty=product.stock_kg)
        if not quantity_validation['valid']:
            flash(f'❌ {quantity_validation["error"]}', 'error')
            return redirect(url_for('orders.cart'))

        cart = session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            cart[product_id_str]['quantity'] = quantity
            session['cart'] = cart
            session.modified = True
            flash(f'✅ मात्रा अपडेट भयो / Quantity updated: {quantity} kg', 'success')
        else:
            flash('❌ कार्टमा उत्पादन फेला परेन / Product not found in cart', 'error')

    return redirect(url_for('orders.cart'))

@orders_bp.route('/remove-from-cart', methods=['POST'])
@login_required
def remove_from_cart():
    """
    Remove item from cart.
    """
    form = RemoveCartForm()
    if form.validate_on_submit():
        product_id = int(form.product_id.data)
        cart = session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            product_name = cart[product_id_str]['name']
            del cart[product_id_str]
            session['cart'] = cart
            session.modified = True
            flash(f'✅ कार्टबाट हटाइयो / Removed from cart: {product_name}', 'success')
        else:
            flash('❌ कार्टमा उत्पादन फेला परेन / Product not found in cart', 'error')

    return redirect(url_for('orders.cart'))

@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Checkout process with payment integration.
    """
    cart = session.get('cart', {})
    if not cart:
        flash('❌ कार्ट खाली छ / Cart is empty', 'warning')
        return redirect(url_for('orders.cart'))

    form = CheckoutForm()
    
    # Calculate cart totals
    cart_items = []
    subtotal = 0
    
    for product_id_str, item in cart.items():
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            # Check stock availability
            if item['quantity'] > product.stock_kg:
                flash(f'❌ {product.name} - केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
                return redirect(url_for('orders.cart'))
            
            item_total = item['quantity'] * product.price
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total': item_total
            })
            subtotal += item_total

    if not cart_items:
        flash('❌ कार्टमा कुनै उपलब्ध उत्पादन छैन / No available products in cart', 'warning')
        return redirect(url_for('orders.cart'))

    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge

    if form.validate_on_submit():
        try:
            # Create order
            order = Order(
                user_id=current_user.id,
                order_number=generate_order_number(),
                total_amount=total,
                delivery_charge=delivery_charge,
                delivery_address=form.delivery_address.data,
                phone=form.phone.data,
                payment_method=form.payment_method.data,
                special_instructions=form.special_instructions.data,
                status='pending'
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID

            # Create order items and update stock
            for item_data in cart_items:
                product = item_data['product']
                quantity = item_data['quantity']
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price,
                    total=quantity * product.price
                )
                db.session.add(order_item)
                
                # Update product stock
                product.stock_kg -= quantity

            # Process payment
            payment_result = process_payment(
                form.payment_method.data,
                total,
                order.order_number
            )

            if payment_result['success']:
                order.payment_status = payment_result.get('payment_status', 'completed')
                order.transaction_id = payment_result.get('transaction_id')
                
                db.session.commit()
                
                # Clear cart
                session.pop('cart', None)
                session.modified = True
                
                flash(payment_result['message'], 'success')
                return redirect(url_for('orders.order_detail', order_id=order.id))
            else:
                db.session.rollback()
                flash(payment_result['message'], 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('अर्डर प्रक्रिया गर्दा समस्या भयो / Error processing order', 'error')

    return render_template('orders/checkout.html',
                         form=form,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_charge=delivery_charge,
                         total=total)

@orders_bp.route('/my-orders')
@login_required
def my_orders():
    """
    Display user's order history.
    """
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id)\
                       .order_by(Order.created_at.desc())\
                       .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('orders/order_list.html', orders=orders)

@orders_bp.route('/<int:order_id>')
@login_required
def order_detail(order_id):
    """
    Display order details.
    """
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns this order
    if order.user_id != current_user.id:
        flash('❌ अनधिकृत पहुँच / Unauthorized access', 'error')
        return redirect(url_for('orders.my_orders'))
    
    return render_template('orders/order_detail.html', order=order)

def process_payment(payment_method, amount, order_number):
    """
    Process payment based on selected method.
    """
    from app.services.payment_service import payment_service
    
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8]}"
    
    if payment_method == 'cod':
        # Cash on Delivery - payment pending until delivery
        payment_service.log_payment_attempt(
            order_number,
            payment_method,
            float(amount),
            'initiated',
            {'transaction_id': transaction_id}
        )
        return {
            'success': True,
            'message': 'अर्डर सफल भयो! घरमा पैसा तिर्नुहोस् / Order placed successfully! Pay on delivery.',
            'payment_status': 'pending',
            'transaction_id': transaction_id
        }
    elif payment_method in ['esewa', 'khalti', 'phonepay', 'mobile_banking', 'bank_transfer']:
        # Digital payments - keep as pending until gateway confirmation
        payment_service.log_payment_attempt(
            order_number,
            payment_method,
            float(amount),
            'initiated',
            {'transaction_id': transaction_id}
        )
        # Simulate digital payment success
        return {
            'success': True,
            'message': f'भुक्तानी सफल भयो! / Payment successful via {payment_method.upper()}!',
            'payment_status': 'pending',
            'transaction_id': transaction_id
        }
    else:
        return {
            'success': False,
            'message': 'अमान्य भुक्तानी विधि / Invalid payment method',
            'payment_status': 'failed'
        }