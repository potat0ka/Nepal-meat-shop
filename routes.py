import os
import uuid
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from app import db
from models import (User, Product, Category, Order, OrderItem, CartItem, Review, DeliveryArea, 
                   Invoice, SalesReport, StockAlert, NotificationTemplate, NotificationLog)
from forms import (LoginForm, RegisterForm, ProductForm, CartForm, CheckoutForm, ReviewForm,
                  OrderStatusForm, CategoryForm, OrderFilterForm, UpdateCartForm, RemoveCartForm)
from utils import save_uploaded_file, generate_order_number
from payment_utils import process_payment, get_payment_instructions

def register_routes(app):
    """Register all application routes."""

    # Home page
    @app.route('/')
    def index():
        """Homepage with featured products and offers."""
        featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(6).all()
        recent_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
        categories = Category.query.filter_by(is_active=True).all()

        return render_template('index.html', 
                             featured_products=featured_products,
                             recent_products=recent_products,
                             categories=categories)

    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash('लगइन सफल भयो / Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('गलत ईमेल वा पासवर्ड / Invalid email or password!', 'error')

        return render_template('auth/login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = RegisterForm()
        if form.validate_on_submit():
            # Check if user already exists
            if User.query.filter_by(email=form.email.data).first():
                flash('यो ईमेल पहिले नै प्रयोग भइसकेको छ / Email already registered!', 'error')
                return render_template('auth/register.html', form=form)

            if User.query.filter_by(username=form.username.data).first():
                flash('यो प्रयोगकर्ता नाम उपलब्ध छैन / Username not available!', 'error')
                return render_template('auth/register.html', form=form)

            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                address=form.address.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('दर्ता सफल भयो! अब लगइन गर्नुहोस् / Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('auth/register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        flash('लगआउट भयो / Logged out successfully!', 'info')
        return redirect(url_for('index'))

    # Product routes
    @app.route('/products')
    def product_list():
        """Product listing with filters."""
        # Get filter parameters
        category_id = request.args.get('category', type=int)
        meat_type = request.args.get('meat_type')
        preparation_type = request.args.get('preparation_type')
        sort_by = request.args.get('sort', 'name')

        # Build query
        query = Product.query.filter_by(is_active=True)

        if category_id:
            query = query.filter_by(category_id=category_id)
        if meat_type:
            query = query.filter_by(meat_type=meat_type)
        if preparation_type:
            query = query.filter_by(preparation_type=preparation_type)

        # Apply sorting
        if sort_by == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'newest':
            query = query.order_by(Product.created_at.desc())
        else:
            query = query.order_by(Product.name.asc())

        products = query.all()
        categories = Category.query.filter_by(is_active=True).all()

        return render_template('products/list.html', 
                             products=products, 
                             categories=categories,
                             current_category=category_id,
                             current_meat_type=meat_type,
                             current_preparation_type=preparation_type,
                             current_sort=sort_by)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        """Product detail page."""
        product = Product.query.get_or_404(product_id)
        reviews = Review.query.filter_by(product_id=product_id, is_approved=True).order_by(Review.created_at.desc()).all()
        related_products = Product.query.filter_by(category_id=product.category_id, is_active=True).filter(Product.id != product_id).limit(4).all()

        form = CartForm()
        review_form = ReviewForm()

        return render_template('products/detail.html', 
                             product=product, 
                             reviews=reviews,
                             related_products=related_products,
                             form=form,
                             review_form=review_form)

    
    @app.route('/add_to_cart', methods=['POST'])
    def add_to_cart():
        """Add item to cart using Flask session."""
        if not current_user.is_authenticated:
            flash('कृपया पहिले लगइन गर्नुहोस् / Please login first', 'warning')
            return redirect(url_for('login'))

        form = CartForm()
        
        # Get product_id from form data for better debugging
        product_id_str = request.form.get('product_id', '')
        quantity_str = request.form.get('quantity', '')
        
        # Debug information
        print(f"DEBUG: product_id from form: '{product_id_str}'")
        print(f"DEBUG: quantity from form: '{quantity_str}'")
        print(f"DEBUG: form.product_id.data: '{form.product_id.data}'")
        print(f"DEBUG: form.quantity.data: '{form.quantity.data}'")
        print(f"DEBUG: form.errors: {form.errors}")
        
        if form.validate_on_submit():
            try:
                product_id = int(form.product_id.data)
                quantity = float(form.quantity.data)
            except (ValueError, TypeError):
                flash('❌ गलत डेटा / Invalid data provided', 'error')
                return redirect(url_for('product_list'))

            # Get product details
            product = Product.query.get_or_404(product_id)

            # Validate minimum order quantity (set to 2kg)
            min_order = 2.0
            if quantity < min_order:
                flash(f'❌ न्यूनतम अर्डर {min_order} केजी हुनुपर्छ / Minimum order is {min_order} kg', 'error')
                return redirect(url_for('product_detail', product_id=product_id))

            # Validate stock availability
            if quantity > product.stock_kg:
                flash(f'❌ केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
                return redirect(url_for('product_detail', product_id=product_id))

            # Initialize cart in session if it doesn't exist
            if 'cart' not in session:
                session['cart'] = {}

            cart = session['cart']
            product_id_str = str(product_id)

            # Check if product already in cart
            if product_id_str in cart:
                # Add to existing quantity but check total doesn't exceed stock
                new_quantity = cart[product_id_str]['quantity'] + quantity
                if new_quantity > product.stock_kg:
                    flash(f'❌ कुल मात्रा {product.stock_kg} केजीभन्दा बढी हुन सक्दैन / Total quantity cannot exceed {product.stock_kg} kg', 'error')
                    return redirect(url_for('product_detail', product_id=product_id))

                cart[product_id_str]['quantity'] = new_quantity
                flash(f'✅ कार्टमा मात्रा अपडेट भयो / Cart quantity updated: {new_quantity} kg', 'success')
            else:
                # Add new item to cart
                cart[product_id_str] = {
                    'product_id': product_id,
                    'name': product.name,
                    'name_nepali': product.name_nepali,
                    'price': product.price,
                    'quantity': quantity,
                    'image_url': product.image_url
                }
                flash(f'✅ कार्टमा थपियो / Added to cart: {product.name} ({quantity} kg)', 'success')

            # Save updated cart to session
            session['cart'] = cart
            session.modified = True

            return redirect(url_for('cart'))

        # If form validation fails, show errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'❌ {error}', 'error')

        # Try to redirect back to the product page if we have a valid product_id
        try:
            if product_id_str and product_id_str != '':
                product_id = int(product_id_str)
                return redirect(url_for('product_detail', product_id=product_id))
        except (ValueError, TypeError):
            pass
        
        return redirect(url_for('product_list'))

    @app.route('/update_cart', methods=['POST'])
    def update_cart():
        """Update cart item quantity."""
        if not current_user.is_authenticated:
            flash('कृपया पहिले लगइन गर्नुहोस् / Please login first', 'warning')
            return redirect(url_for('login'))

        form = UpdateCartForm()
        if form.validate_on_submit():
            product_id = int(form.product_id.data)
            quantity = float(form.quantity.data)

            product = Product.query.get_or_404(product_id)

            # Validate minimum order quantity
            if quantity < product.min_order_kg:
                flash(f'❌ न्यूनतम अर्डर {product.min_order_kg} केजी हुनुपर्छ / Minimum order is {product.min_order_kg} kg', 'error')
                return redirect(url_for('cart'))

            # Validate stock availability
            if quantity > product.stock_kg:
                flash(f'❌ केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
                return redirect(url_for('cart'))

            cart = session.get('cart', {})
            product_id_str = str(product_id)

            if product_id_str in cart:
                cart[product_id_str]['quantity'] = quantity
                session['cart'] = cart
                session.modified = True
                flash(f'✅ मात्रा अपडेट भयो / Quantity updated: {quantity} kg', 'success')
            else:
                flash('❌ कार्टमा उत्पादन फेला परेन / Product not found in cart', 'error')

        return redirect(url_for('cart'))

    @app.route('/remove_from_cart', methods=['POST'])
    def remove_from_cart():
        """Remove item from cart."""
        if not current_user.is_authenticated:
            flash('कृपया पहिले लगइन गर्नुहोस् / Please login first', 'warning')
            return redirect(url_for('login'))

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

        return redirect(url_for('cart'))

    @app.route('/cart')
    def cart():
        """Display cart contents."""
        if not current_user.is_authenticated:
            flash('कृपया पहिले लगइन गर्नुहोस् / Please login first', 'warning')
            return redirect(url_for('login'))

        cart = session.get('cart', {})
        cart_items = []
        total = 0

        for product_id_str, item in cart.items():
            # Get fresh product data
            product = Product.query.get(int(product_id_str))
            if product and product.is_active:
                item_total = item['quantity'] * product.price
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'total': item_total
                })
                total += item_total

        return render_template('cart/cart.html', cart_items=cart_items, total=total)

    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        """Checkout process with payment integration."""
        cart = session.get('cart', {})
        if not cart:
            flash('❌ कार्ट खाली छ / Cart is empty', 'warning')
            return redirect(url_for('cart'))

        form = CheckoutForm()
        
        # Calculate cart total for display
        cart_total = 0
        cart_items = []
        for product_id_str, item in cart.items():
            product = Product.query.get(int(product_id_str))
            if product and product.is_active:
                item_total = item['quantity'] * product.price
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'total': item_total
                })
                cart_total += item_total
        
        if form.validate_on_submit():
            # Create order
            order = Order(
                user_id=current_user.id,
                payment_method=form.payment_method.data,
                delivery_address=form.delivery_address.data,
                delivery_phone=form.delivery_phone.data,
                special_instructions=form.special_instructions.data
            )
            order.generate_order_number()
            
            total_amount = 0
            order_items = []

            # Process cart items
            for product_id_str, item in cart.items():
                product = Product.query.get(int(product_id_str))
                if product and product.is_active:
                    # Check stock availability
                    if item['quantity'] > product.stock_kg:
                        flash(f'❌ {product.name} स्टकमा छैन / {product.name} out of stock', 'error')
                        return render_template('orders/checkout.html', form=form, cart_items=cart_items, cart_total=cart_total)

                    # Create order item
                    order_item = OrderItem(
                        product_id=product.id,
                        quantity_kg=item['quantity'],
                        price_per_kg=product.price,
                        total_price=item['quantity'] * product.price
                    )
                    order_items.append(order_item)
                    total_amount += order_item.total_price

            order.total_amount = total_amount
            order.order_items = order_items

            # Process payment
            payment_result = process_payment(
                payment_method=form.payment_method.data,
                amount=total_amount,
                order_number=order.order_number
            )

            if payment_result['success']:
                # Payment successful or COD
                order.payment_status = payment_result['payment_status']
                if payment_result.get('transaction_id'):
                    order.transaction_id = payment_result['transaction_id']
                
                # Update stock only after successful payment
                for product_id_str, item in cart.items():
                    product = Product.query.get(int(product_id_str))
                    if product and product.is_active:
                        product.stock_kg -= item['quantity']

                # Save order
                db.session.add(order)
                db.session.commit()

                # Clear cart
                session.pop('cart', None)
                session.modified = True

                flash(f'✅ {payment_result["message"]}', 'success')
                return redirect(url_for('order_detail', order_id=order.id))
            else:
                # Payment failed
                flash(f'❌ {payment_result["message"]}', 'error')
                return render_template('orders/checkout.html', form=form, cart_items=cart_items, cart_total=cart_total)

        return render_template('orders/checkout.html', form=form, cart_items=cart_items, cart_total=cart_total)

    @app.route('/orders')
    @login_required
    def order_list():
        """List user's orders."""
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template('orders/order_list.html', orders=orders)

    @app.route('/order/<int:order_id>')
    @login_required
    def order_detail(order_id):
        """Order detail page."""
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns this order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            flash('❌ अनधिकृत पहुँच / Unauthorized access', 'error')
            return redirect(url_for('order_list'))

        return render_template('orders/order_detail.html', order=order)

    @app.route('/invoice/<int:order_id>')
    @login_required
    def generate_invoice(order_id):
        """Generate invoice for an order."""
        order = Order.query.get_or_404(order_id)
        
        # Check if user owns this order or is admin
        if order.user_id != current_user.id and not current_user.is_admin:
            flash('❌ अनधिकृत पहुँच / Unauthorized access', 'error')
            return redirect(url_for('order_list'))

        # Check if invoice already exists
        invoice = Invoice.query.filter_by(order_id=order.id).first()
        
        if not invoice:
            # Create new invoice
            invoice = Invoice(
                order_id=order.id,
                subtotal=order.total_amount,
                tax_amount=0,  # No tax for now
                delivery_charge=0,  # Free delivery for now
                total_amount=order.total_amount,
                is_paid=(order.payment_status == 'paid')
            )
            invoice.generate_invoice_number()
            db.session.add(invoice)
            db.session.commit()

        return render_template('orders/invoice.html', order=order, invoice=invoice)

    # User profile routes
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page."""
        return render_template('user/profile.html')

    @app.route('/update_profile', methods=['POST'])
    @login_required
    def update_profile():
        """Update user profile information."""
        try:
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not full_name or len(full_name) < 2:
                flash('❌ पूरा नाम आवश्यक छ / Full name is required (min 2 characters)', 'error')
                return redirect(url_for('profile'))
            
            if not phone or len(phone) < 10:
                flash('❌ वैध फोन नम्बर आवश्यक छ / Valid phone number is required (min 10 digits)', 'error')
                return redirect(url_for('profile'))
            
            # Update user information
            current_user.full_name = full_name
            current_user.phone = phone
            current_user.address = address if address else None
            
            # Save to database
            db.session.commit()
            
            flash('✅ प्रोफाइल अपडेट भयो / Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash('❌ प्रोफाइल अपडेट गर्न सकिएन / Failed to update profile', 'error')
            db.session.rollback()
            return redirect(url_for('profile'))

    @app.route('/change_password', methods=['POST'])
    @login_required
    def change_password():
        """Change user password."""
        try:
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('❌ हालको पासवर्ड गलत छ / Current password is incorrect', 'error')
                return redirect(url_for('profile'))
            
            # Validate new password
            if len(new_password) < 6:
                flash('❌ नयाँ पासवर्ड कम्तिमा ६ अक्षरको हुनुपर्छ / New password must be at least 6 characters', 'error')
                return redirect(url_for('profile'))
            
            # Validate password confirmation
            if new_password != confirm_password:
                flash('❌ नयाँ पासवर्डहरू मेल खाँदैनन् / New passwords do not match', 'error')
                return redirect(url_for('profile'))
            
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            
            flash('✅ पासवर्ड परिवर्तन भयो / Password changed successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash('❌ पासवर्ड परिवर्तन गर्न सकिएन / Failed to change password', 'error')
            db.session.rollback()
            return redirect(url_for('profile'))

    # Admin routes
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Admin dashboard."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        # Get dashboard statistics
        total_orders = Order.query.count()
        total_products = Product.query.count()
        total_users = User.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()

        return render_template('admin/dashboard.html', 
                             total_orders=total_orders,
                             total_products=total_products,
                             total_users=total_users,
                             pending_orders=pending_orders)

    @app.route('/admin/products')
    @login_required
    def admin_products():
        """Admin products management."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('admin/products.html', products=products)

    @app.route('/admin/product/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_product():
        """Add new product."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        form = ProductForm()
        form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]

        if form.validate_on_submit():
            # Handle image upload
            image_url = None
            if form.image.data:
                image_url = save_uploaded_file(form.image.data, 'products')

            product = Product(
                name=form.name.data,
                name_nepali=form.name_nepali.data,
                description=form.description.data,
                price=form.price.data,
                category_id=form.category_id.data,
                meat_type=form.meat_type.data,
                preparation_type=form.preparation_type.data,
                stock_kg=form.stock_kg.data,
                min_order_kg=form.min_order_kg.data,
                freshness_hours=form.freshness_hours.data,
                cooking_tips=form.cooking_tips.data,
                is_featured=form.is_featured.data,
                image_url=image_url
            )

            db.session.add(product)
            db.session.commit()

            flash('✅ उत्पादन थपियो / Product added successfully!', 'success')
            return redirect(url_for('admin_products'))

        return render_template('admin/product_form.html', form=form, title='Add Product')

    @app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_product(product_id):
        """Edit existing product."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        form = ProductForm(obj=product)
        form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]

        if form.validate_on_submit():
            # Handle image upload
            if form.image.data:
                image_url = save_uploaded_file(form.image.data, 'products')
                product.image_url = image_url

            # Update product fields
            product.name = form.name.data
            product.name_nepali = form.name_nepali.data
            product.description = form.description.data
            product.price = form.price.data
            product.category_id = form.category_id.data
            product.meat_type = form.meat_type.data
            product.preparation_type = form.preparation_type.data
            product.stock_kg = form.stock_kg.data
            product.min_order_kg = form.min_order_kg.data
            product.freshness_hours = form.freshness_hours.data
            product.cooking_tips = form.cooking_tips.data
            product.is_featured = form.is_featured.data
            product.updated_at = datetime.utcnow()

            db.session.commit()

            flash('✅ उत्पादन अपडेट भयो / Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))

        return render_template('admin/product_form.html', form=form, title='Edit Product', product=product)

    @app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
    @login_required
    def admin_delete_product(product_id):
        """Delete product."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        
        # Check if product has any orders
        if product.order_items:
            flash('❌ यो उत्पादनमा अर्डरहरू छन्, डिलीट गर्न सकिँदैन / Cannot delete product with existing orders', 'error')
            return redirect(url_for('admin_products'))

        # Soft delete - just mark as inactive
        product.is_active = False
        db.session.commit()

        flash('✅ उत्पादन डिलीट भयो / Product deleted successfully!', 'success')
        return redirect(url_for('admin_products'))

    @app.route('/admin/product/toggle-featured/<int:product_id>', methods=['POST'])
    @login_required
    def admin_toggle_featured(product_id):
        """Toggle product featured status."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        product.is_featured = not product.is_featured
        product.updated_at = datetime.utcnow()
        
        db.session.commit()

        status = 'featured' if product.is_featured else 'removed from featured'
        flash(f'✅ उत्पादन {status} भयो / Product {status} successfully!', 'success')
        return redirect(url_for('admin_products'))

    @app.route('/admin/orders')
    @login_required
    def admin_orders():
        """Admin orders management."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template('admin/orders.html', orders=orders)

    @app.route('/admin/users')
    @login_required
    def admin_users():
        """Admin users management."""
        if not current_user.is_admin:
            flash('❌ एडमिन पहुँच आवश्यक / Admin access required', 'error')
            return redirect(url_for('index'))

        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin/users.html', users=users)

    # File upload routes
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
