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
        if form.validate_on_submit():
            product_id = int(form.product_id.data)
            quantity = float(form.quantity.data)

            # Get product details
            product = Product.query.get_or_404(product_id)

            # Validate minimum order quantity
            if quantity < product.min_order_kg:
                flash(f'❌ न्यूनतम अर्डर {product.min_order_kg} केजी हुनुपर्छ / Minimum order is {product.min_order_kg} kg', 'error')
                return redirect(url_for('product_detail', id=product_id))

            # Validate stock availability
            if quantity > product.stock_kg:
                flash(f'❌ केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
                return redirect(url_for('product_detail', id=product_id))

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
                    return redirect(url_for('product_detail', id=product_id))

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

        return redirect(url_for('product_detail', id=form.product_id.data))

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
        total_amount = 0

        # Convert cart items to display format
        for product_id_str, item in cart.items():
            product = Product.query.get(int(product_id_str))
            if product and product.is_active:
                # Check if quantity still valid against current stock
                if item['quantity'] > product.stock_kg:
                    item['quantity'] = product.stock_kg
                    cart[product_id_str]['quantity'] = product.stock_kg
                    session['cart'] = cart
                    session.modified = True
                    flash(f'⚠️ {product.name} को मात्रा स्टक अनुसार समायोजन गरियो / Quantity adjusted for {product.name}', 'warning')

                subtotal = item['quantity'] * product.price
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })
                total_amount += subtotal
            else:
                # Remove invalid/inactive products from cart
                del cart[product_id_str]
                session['cart'] = cart
                session.modified = True

        update_form = UpdateCartForm()
        remove_form = RemoveCartForm()

        return render_template('cart/cart.html', 
                             cart_items=cart_items, 
                             total_amount=total_amount,
                             update_form=update_form,
                             remove_form=remove_form)

    
    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        """Checkout page with order processing."""
        cart = session.get('cart', {})
        if not cart:
            flash('आपनो कार्ट खाली छ / Your cart is empty', 'warning')
            return redirect(url_for('products'))

        form = CheckoutForm()

        # Pre-fill user information
        if request.method == 'GET':
            form.delivery_address.data = current_user.address
            form.delivery_phone.data = current_user.phone

        # Calculate cart totals
        cart_items = []
        total_amount = 0

        for product_id_str, item in cart.items():
            product = Product.query.get(int(product_id_str))
            if product and product.is_active:
                # Validate stock availability before checkout
                if item['quantity'] > product.stock_kg:
                    flash(f'❌ {product.name} - केवल {product.stock_kg} केजी स्टकमा छ / Only {product.stock_kg} kg in stock', 'error')
                    return redirect(url_for('cart'))

                subtotal = item['quantity'] * product.price
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })
                total_amount += subtotal

        if form.validate_on_submit():
            try:
                # Create new order
                order = Order(
                    user_id=current_user.id,
                    total_amount=total_amount,
                    payment_method=form.payment_method.data,
                    delivery_address=form.delivery_address.data,
                    delivery_phone=form.delivery_phone.data,
                    special_instructions=form.special_instructions.data
                )
                order.generate_order_number()

                db.session.add(order)
                db.session.flush()  # Get order ID

                # Create order items and update stock
                for item in cart_items:
                    product = item['product']
                    quantity = item['quantity']

                    # Create order item
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity_kg=quantity,
                        price_per_kg=product.price,
                        total_price=quantity * product.price
                    )
                    db.session.add(order_item)

                    # Update product stock
                    product.stock_kg -= quantity

                    # Check if stock goes below minimum alert threshold
                    if product.stock_kg <= 5.0:  # Alert threshold
                        flash(f'⚠️ स्टक कम छ / Low stock alert for {product.name}: {product.stock_kg} kg remaining', 'warning')

                db.session.commit()

                # Clear cart
                session.pop('cart', None)
                session.modified = True

                flash('✅ अर्डर सफलतापूर्वक प्लेस भयो / Order placed successfully!', 'success')
                return redirect(url_for('order_confirmation', order_number=order.order_number))

            except Exception as e:
                db.session.rollback()
                flash(f'❌ अर्डर प्लेस गर्न समस्या भयो / Error placing order: {str(e)}', 'error')

        return render_template('cart/checkout.html', 
                             form=form, 
                             cart_items=cart_items, 
                             total_amount=total_amount)

    @app.route('/order-confirmation/<order_number>')
    @login_required
    def order_confirmation(order_number):
        """Order confirmation page."""
        order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
        return render_template('cart/order_confirmation.html', order=order)

    # Order routes
    @app.route('/orders')
    @login_required
    def user_orders():
        """User order history."""
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template('user/orders.html', orders=orders)

    @app.route('/order/<int:order_id>')
    @login_required
    def order_detail(order_id):
        """Order detail page."""
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        return render_template('user/order_detail.html', order=order)

    # User dashboard
    @app.route('/dashboard')
    @login_required
    def user_dashboard():
        """User dashboard."""
        recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
        return render_template('user/dashboard.html', recent_orders=recent_orders)

    # Review routes
    @app.route('/add_review/<int:product_id>', methods=['POST'])
    @login_required
    def add_review(product_id):
        """Add product review."""
        form = ReviewForm()
        if form.validate_on_submit():
            # Check if user has already reviewed this product
            existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if existing_review:
                flash('तपाईंले यो उत्पादनको समीक्षा पहिले नै गर्नुभएको छ / You have already reviewed this product!', 'error')
                return redirect(url_for('product_detail', product_id=product_id))

            # Handle image upload
            image_url = None
            if form.image.data:
                image_url = save_uploaded_file(form.image.data, 'reviews')

            review = Review(
                user_id=current_user.id,
                product_id=product_id,
                rating=form.rating.data,
                comment=form.comment.data,
                image_url=image_url
            )

            db.session.add(review)
            db.session.commit()

            flash('समीक्षाको लागि धन्यवाद / Thank you for your review!', 'success')

        return redirect(url_for('product_detail', product_id=product_id))

    # Admin routes
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Enhanced admin dashboard with sales analytics."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        from datetime import date, timedelta
        from sqlalchemy import func

        # Date ranges for analytics
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Basic statistics
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_users = User.query.filter_by(is_admin=False).count()

        # Sales analytics
        today_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            func.date(Order.created_at) == today,
            Order.status != 'cancelled'
        ).scalar() or 0

        week_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= week_ago,
            Order.status != 'cancelled'
        ).scalar() or 0

        month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= month_ago,
            Order.status != 'cancelled'
        ).scalar() or 0

        # Top selling products (last 30 days)
        top_products = db.session.query(
            Product.name, 
            func.sum(OrderItem.quantity_kg).label('total_sold')
        ).join(OrderItem).join(Order).filter(
            Order.created_at >= month_ago,
            Order.status != 'cancelled'
        ).group_by(Product.id).order_by(
            func.sum(OrderItem.quantity_kg).desc()
        ).limit(5).all()

        # Order status breakdown
        status_counts = db.session.query(
            Order.status, 
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()

        # Low stock alerts (products with less than 5kg stock)
        low_stock_products = Product.query.filter(
            Product.stock_kg <= 5,
            Product.is_active == True
        ).order_by(Product.stock_kg.asc()).all()

        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

        return render_template('admin/dashboard.html',
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             total_products=total_products,
                             total_users=total_users,
                             today_revenue=today_revenue,
                             week_revenue=week_revenue,
                             month_revenue=month_revenue,
                             top_products=top_products,
                             status_counts=status_counts,
                             low_stock_products=low_stock_products,
                             recent_orders=recent_orders,
                             current_time=datetime.now())

    @app.route('/admin/products')
    @login_required
    def admin_products():
        """Admin product management."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('admin/products.html', products=products)

    
    @app.route('/admin/products/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_product():
        """Add new product with image upload."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        form = ProductForm()

        # Populate category choices
        categories = Category.query.filter_by(is_active=True).all()
        form.category_id.choices = [(c.id, f"{c.name} / {c.name_nepali}") for c in categories]

        if form.validate_on_submit():
            try:
                # Handle image upload
                image_url = None
                if form.image.data:
                    image_file = form.image.data
                    filename = secure_filename(image_file.filename)

                    # Create unique filename to avoid conflicts
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name_part = secure_filename(form.name.data.replace(' ', '_').lower())
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{name_part}_{timestamp}.{file_ext}"

                    # Save image to uploads folder
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    image_file.save(upload_path)
                    image_url = f"uploads/{new_filename}"

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
                    is_active=form.is_active.data,
                    image_url=image_url
                )

                db.session.add(product)
                db.session.commit()
                flash('✅ उत्पादन सफलतापूर्वक थपियो / Product added successfully!', 'success')
                return redirect(url_for('admin_products'))

            except Exception as e:
                db.session.rollback()
                flash(f'❌ त्रुटि भयो / Error occurred: {str(e)}', 'error')

        return render_template('admin/product_form.html', form=form, title='Add Product')

    @app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_product(product_id):
        """Edit product."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        form = ProductForm(obj=product)
        form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]

        if form.validate_on_submit():
            # Handle image upload
            if form.image.data:
                product.image_url = save_uploaded_file(form.image.data, 'products')

            form.populate_obj(product)
            product.updated_at = datetime.utcnow()

            db.session.commit()

            flash('उत्पादन अपडेट भयो / Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))

        return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')

    @app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
    @login_required
    def admin_delete_product(product_id):
        """Delete product (soft delete by setting inactive)."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        product.is_active = False
        product.updated_at = datetime.utcnow()

        db.session.commit()

        flash(f'उत्पादन डिलिट भयो / Product {product.name} deleted successfully!', 'success')
        return redirect(url_for('admin_products'))

    @app.route('/admin/product/toggle/<int:product_id>', methods=['POST'])
    @login_required
    def admin_toggle_product(product_id):
        """Toggle product active status."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        product.is_active = not product.is_active
        product.updated_at = datetime.utcnow()

        db.session.commit()

        status = 'activated' if product.is_active else 'deactivated'
        flash(f'उत्पादन {status} / Product {status} successfully!', 'success')
        return redirect(url_for('admin_products'))

    @app.route('/admin/orders')
    @login_required
    def admin_orders():
        """Admin order management."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        status_filter = request.args.get('status')

        query = Order.query
        if status_filter:
            query = query.filter_by(status=status_filter)

        orders = query.order_by(Order.created_at.desc()).all()
        return render_template('admin/orders.html', orders=orders, current_status=status_filter)

    @app.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
    @login_required
    def admin_order_detail(order_id):
        """Admin order detail and status update."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        order = Order.query.get_or_404(order_id)
        form = OrderStatusForm(obj=order)

        if form.validate_on_submit():
            old_status = order.status
            order.status = form.status.data
            order.payment_status = form.payment_status.data
            order.updated_at = datetime.utcnow()

            db.session.commit()

            # Send status update notification to customer
            if old_status != order.status:
                try:
                    from notification_utils import send_order_status_update
                    send_order_status_update(order, old_status, order.status)
                except Exception as e:
                    current_app.logger.error(f"Failed to send status update notification: {str(e)}")

            flash('अर्डर स्थिति अपडेट भयो / Order status updated!', 'success')
            return redirect(url_for('admin_orders'))

        return render_template('admin/order_detail.html', order=order, form=form)

    @app.route('/admin/order/quick_update/<int:order_id>/<status>', methods=['POST'])
    @login_required
    def admin_quick_order_update(order_id, status):
        """Quick order status update."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        order = Order.query.get_or_404(order_id)
        old_status = order.status
        order.status = status
        order.updated_at = datetime.utcnow()

        db.session.commit()

        # Send status update notification
        try:
            from notification_utils import send_order_status_update
            send_order_status_update(order, old_status, status)
        except Exception as e:
            current_app.logger.error(f"Failed to send status update notification: {str(e)}")

        flash(f'अर्डर स्थिति अपडेट भयो / Order status updated to {status.replace("_", " ")}!', 'success')
        return redirect(url_for('admin_orders'))

    @app.route('/admin/orders/bulk_action', methods=['POST'])
    @login_required
    def admin_bulk_order_action():
        """Execute bulk actions on orders."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        action = request.form.get('action')
        order_ids = request.form.getlist('order_ids')

        if not action or not order_ids:
            flash('अवैध बल्क एक्शन / Invalid bulk action!', 'error')
            return redirect(url_for('admin_orders'))

        success_count = 0

        if action in ['confirm', 'processing', 'out_for_delivery', 'delivered']:
            # Status update actions
            status_map = {
                'confirm': 'confirmed',
                'processing': 'processing',
                'out_for_delivery': 'out_for_delivery',
                'delivered': 'delivered'
            }
            new_status = status_map[action]

            for order_id in order_ids:
                try:
                    order = Order.query.get(int(order_id))
                    if order:
                        old_status = order.status
                        order.status = new_status
                        order.updated_at = datetime.utcnow()

                        # Send notification
                        try:
                            from notification_utils import send_order_status_update
                            send_order_status_update(order, old_status, new_status)
                        except Exception as e:
                            current_app.logger.error(f"Failed to send notification for order {order_id}: {str(e)}")

                        success_count += 1
                except Exception as e:
                    current_app.logger.error(f"Failed to update order {order_id}: {str(e)}")

            db.session.commit()
            flash(f'{success_count} अर्डरहरू अपडेट भए / {success_count} orders updated to {new_status.replace("_", " ")}!', 'success')

        elif action == 'export_selected':
            # Export selected orders
            import csv
            from io import StringIO
            from flask import make_response

            orders = Order.query.filter(Order.id.in_(order_ids)).all()

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Order ID', 'Order Number', 'Customer', 'Email', 'Phone', 'Total Amount', 'Status', 'Payment Method', 'Created Date'])

            for order in orders:
                writer.writerow([
                    order.id,
                    order.order_number,
                    order.customer.full_name,
                    order.customer.email,
                    order.delivery_phone,
                    f"NPR {order.total_amount:.2f}",
                    order.status,
                    order.payment_method,
                    order.created_at.strftime('%Y-%m-%d %H:%M')
                ])

            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=selected_orders_export.csv'
            return response

        return redirect(url_for('admin_orders'))

    # Admin Invoice Management
    @app.route('/admin/invoice/<int:order_id>')
    @login_required
    def admin_generate_invoice(order_id):
        """Generate invoice for order."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        order = Order.query.get_or_404(order_id)

        # Create or get existing invoice
        invoice = Invoice.query.filter_by(order_id=order_id).first()
        if not invoice:
            # Calculate invoice amounts
            subtotal = order.total_amount
            tax_rate = 0.13  # 13% VAT
            tax_amount = subtotal * tax_rate
            delivery_charge = 50.0  # Default delivery charge

            # Adjust delivery charge based on order amount
            if subtotal >= 2000:  # Free delivery for orders above 2000
                delivery_charge = 0
            elif subtotal >= 1000:  # Reduced delivery for orders above 1000
                delivery_charge = 25

            total_amount = subtotal + tax_amount + delivery_charge

            invoice = Invoice(
                order_id=order_id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                delivery_charge=delivery_charge,
                total_amount=total_amount,
                notes=f"Invoice for order {order.order_number}"
            )
            invoice.generate_invoice_number()
            db.session.add(invoice)
            db.session.commit()

            flash('चलान सिर्जना गरियो / Invoice generated successfully!', 'success')

        return render_template('admin/invoice.html', invoice=invoice, order=order)

    @app.route('/admin/invoice/edit/<int:invoice_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_invoice(invoice_id):
        """Edit invoice details."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        invoice = Invoice.query.get_or_404(invoice_id)
        form = InvoiceForm(obj=invoice)

        if form.validate_on_submit():
            invoice.notes = form.notes.data
            invoice.delivery_charge = form.delivery_charge.data

            # Recalculate total with new tax rate and delivery charge
            tax_rate = form.tax_rate.data / 100  # Convert percentage to decimal
            invoice.tax_amount = invoice.subtotal * tax_rate
            invoice.total_amount = invoice.subtotal + invoice.tax_amount + invoice.delivery_charge

            db.session.commit()

            flash('चलान अपडेट भयो / Invoice updated successfully!', 'success')
            return redirect(url_for('admin_generate_invoice', order_id=invoice.order_id))

        return render_template('admin/invoice_form.html', form=form, invoice=invoice)

    @app.route('/admin/invoice/download/<int:invoice_id>')
    @login_required
    def admin_download_invoice(invoice_id):
        """Download invoice as PDF."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        invoice = Invoice.query.get_or_404(invoice_id)
        # For now, render as HTML with print styles - in production, you'd generate PDF
        return render_template('admin/invoice.html', invoice=invoice, order=invoice.order, print_mode=True)

    @app.route('/admin/invoice/mark_paid/<int:invoice_id>', methods=['POST'])
    @login_required
    def admin_mark_invoice_paid(invoice_id):
        """Mark invoice as paid."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        invoice = Invoice.query.get_or_404(invoice_id)
        invoice.is_paid = True

        # Also update order payment status
        invoice.order.payment_status = 'paid'

        db.session.commit()

        flash('चलान भुक्तानी गरिएको छ / Invoice marked as paid!', 'success')
        return redirect(url_for('admin_generate_invoice', order_id=invoice.order.order_id))

    # Admin Reports and Analytics
    @app.route('/admin/reports')
    @login_required
    def admin_reports():
        """Admin reports dashboard."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        from datetime import date, timedelta
        from sqlalchemy import func

        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Sales statistics
        today_orders = Order.query.filter(func.date(Order.created_at) == today).count()
        today_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            func.date(Order.created_at) == today).scalar() or 0

        week_orders = Order.query.filter(Order.created_at >= week_ago).count()
        week_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= week_ago).scalar() or 0

        month_orders = Order.query.filter(Order.created_at >= month_ago).count()
        month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= month_ago).scalar() or 0

        # Top selling products
        top_products = db.session.query(
            Product.name, 
            func.sum(OrderItem.quantity_kg).label('total_sold')
        ).join(OrderItem).group_by(Product.id).order_by(
            func.sum(OrderItem.quantity_kg).desc()
        ).limit(5).all()

        # Order status breakdown
        status_counts = db.session.query(
            Order.status, 
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()

        # Low stock alerts
        low_stock_products = Product.query.filter(Product.stock_kg <= 5).all()

        return render_template('admin/reports.html', 
                             today_orders=today_orders, today_revenue=today_revenue,
                             week_orders=week_orders, week_revenue=week_revenue,
                             month_orders=month_orders, month_revenue=month_revenue,
                             top_products=top_products, status_counts=status_counts,
                             low_stock_products=low_stock_products)

    @app.route('/admin/reports/export/<report_type>')
    @login_required
    def admin_export_report(report_type):
        """Export reports as CSV."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        import csv
        from io import StringIO
        from flask import make_response

        if report_type == 'orders':
            orders = Order.query.order_by(Order.created_at.desc()).all()

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Order ID', 'Customer', 'Total Amount', 'Status', 'Payment Method', 'Created Date'])

            for order in orders:
                writer.writerow([
                    order.order_number,
                    order.customer.full_name,
                    f"NPR {order.total_amount:.2f}",
                    order.status,
                    order.payment_method,
                    order.created_at.strftime('%Y-%m-%d %H:%M')
                ])

            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=orders_export.csv'
            return response

        return redirect(url_for('admin_reports'))

    # Admin Stock Management
    @app.route('/admin/stock')
    @login_required
    def admin_stock():
        """Stock management dashboard."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        products = Product.query.order_by(Product.stock_kg.asc()).all()
        low_stock_count = Product.query.filter(Product.stock_kg <= 5).count()

        return render_template('admin/stock.html', products=products, low_stock_count=low_stock_count)

    @app.route('/admin/stock/update/<int:product_id>', methods=['POST'])
    @login_required
    def admin_update_stock(product_id):
        """Update product stock."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        product = Product.query.get_or_404(product_id)
        new_stock = request.form.get('stock_kg', type=float)

        if new_stock is not None and new_stock >= 0:
            product.stock_kg = new_stock
            product.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f'स्टक अपडेट भयो / Stock updated for {product.name}!', 'success')
        else:
            flash('अवैध स्टक मान / Invalid stock value!', 'error')

        return redirect(url_for('admin_stock'))

    # Admin Category Management
    @app.route('/admin/categories')
    @login_required
    def admin_categories():
        """Category management."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        categories = Category.query.all()
        return render_template('admin/categories.html', categories=categories)

    @app.route('/admin/category/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_category():
        """Add new category."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        form = CategoryForm()
        if form.validate_on_submit():
            category = Category(
                name=form.name.data,
                name_nepali=form.name_nepali.data,
                description=form.description.data,
                is_active=form.is_active.data
            )
            db.session.add(category)
            db.session.commit()

            flash('श्रेणी थपियो / Category added successfully!', 'success')
            return redirect(url_for('admin_categories'))

        return render_template('admin/category_form.html', form=form, title='Add Category')

    @app.route('/admin/category/edit/<int:category_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_category(category_id):
        """Edit category."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        category = Category.query.get_or_404(category_id)
        form = CategoryForm(obj=category)

        if form.validate_on_submit():
            form.populate_obj(category)
            db.session.commit()

            flash('श्रेणी अपडेट भयो / Category updated successfully!', 'success')
            return redirect(url_for('admin_categories'))

        return render_template('admin/category_form.html', form=form, category=category, title='Edit Category')

    # Admin Customer Management
    @app.route('/admin/customers')
    @login_required
    def admin_customers():
        """Customer management."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        customers = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
        return render_template('admin/customers.html', customers=customers)

    @app.route('/admin/customer/<int:customer_id>')
    @login_required
    def admin_customer_detail(customer_id):
        """Customer detail view."""
        if not current_user.is_admin:
            flash('पहुँच अस्वीकृत / Access denied!', 'error')
            return redirect(url_for('index'))

        customer = User.query.get_or_404(customer_id)
        orders = Order.query.filter_by(user_id=customer_id).order_by(Order.created_at.desc()).all()

        return render_template('admin/customer_detail.html', customer=customer, orders=orders)

    # Contact page
    @app.route('/contact')
    def contact():
        """Contact and support page."""
        return render_template('contact.html')

    # File upload handler
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Initialize default data with modern Flask approach
    initialized = False

    @app.before_request
    def create_default_data():
        """Create default categories and sample products."""
        nonlocal initialized
        if not initialized:
            if Category.query.count() == 0:
                # Create default categories
                categories = [
                    {'name': 'Head Cuts', 'name_nepali': 'टाउको'},
                    {'name': 'Leg Cuts', 'name_nepali': 'खुट्टा'},
                    {'name': 'Stomach Cuts', 'name_nepali': 'पेट'},
                    {'name': 'Combo Packs', 'name_nepali': 'कम्बो प्याक'},
                    {'name': 'Processed Meat', 'name_nepali': 'प्रसिद्ध मासु'},
                    {'name': 'Organs', 'name_nepali': 'मुटु छाती'}
                ]

                for cat_data in categories:
                    category = Category(**cat_data)
                    db.session.add(category)

                db.session.commit()
                print("Default categories created")
            initialized = True