#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Admin Routes
Admin panel routes for user management, product management, and order management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoUser, MongoProduct, MongoOrder
from app.forms.product import ProductForm, CategoryForm
from app.forms.qr_code import QRCodeForm, QRCodeUpdateForm
from app.utils.file_utils import save_uploaded_file, delete_file, validate_image_file
from bson import ObjectId
from datetime import datetime
import json

# Create admin blueprint
mongo_admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_admin_access():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    """Decorator to require full admin access (not sub-admin) for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Full admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator to require staff access (admin, sub-admin, or staff) for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_staff_access():
            flash('Access denied. Staff privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@mongo_admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with overview statistics."""
    try:
        # Get statistics
        total_users = mongo_db.db.users.count_documents({})
        total_products = mongo_db.db.products.count_documents({})
        total_orders = mongo_db.db.orders.count_documents({})
        pending_orders = mongo_db.db.orders.count_documents({'status': 'pending'})
        
        # Get recent orders
        recent_orders = list(mongo_db.db.orders.find().sort('order_date', -1).limit(5))
        
        stats = {
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'recent_orders': recent_orders
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@mongo_admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    """Admin user management page."""
    try:
        users_data = list(mongo_db.db.users.find())
        users = [MongoUser(user_data) for user_data in users_data]
        return render_template('admin/users.html', users=users)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Edit user details page."""
    try:
        # Validate user_id
        if not user_id or user_id == 'None':
            flash('Invalid user ID.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            flash('Invalid user ID format.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        user_data = mongo_db.db.users.find_one({'_id': user_object_id})
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        user = MongoUser(user_data)
        
        if request.method == 'POST':
            try:
                # Check permissions
                if not current_user.can_manage_users():
                    flash('Access denied. You cannot manage users.', 'error')
                    return redirect(url_for('admin.admin_users'))
                
                # Get form data
                full_name = request.form.get('full_name', '').strip()
                email = request.form.get('email', '').strip()
                phone = request.form.get('phone', '').strip()
                address = request.form.get('address', '').strip()
                new_password = request.form.get('new_password', '').strip()
                
                # Validate required fields
                if not full_name or not email or not phone:
                    flash('Full name, email, and phone are required.', 'error')
                    return render_template('admin/user_edit.html', user=user)
                
                # Check if email is already taken by another user
                existing_user = mongo_db.db.users.find_one({
                    'email': email,
                    '_id': {'$ne': user_object_id}
                })
                if existing_user:
                    flash('Email address is already in use by another user.', 'error')
                    return render_template('admin/user_edit.html', user=user)
                
                # Prepare update data
                update_data = {
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'last_updated': datetime.utcnow()
                }
                
                # Handle password update
                if new_password:
                    if len(new_password) < 6:
                        flash('Password must be at least 6 characters long.', 'error')
                        return render_template('admin/user_edit.html', user=user)
                    update_data['password'] = generate_password_hash(new_password)
                
                # Handle profile picture upload
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename:
                        try:
                            # Validate image file
                            if not validate_image_file(file):
                                flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                                return render_template('admin/user_edit.html', user=user)
                            
                            # Delete old profile image if exists
                            if user.profile_image:
                                delete_file(user.profile_image)
                            
                            # Save new profile image
                            filename = save_uploaded_file(file, 'profiles')
                            if filename:
                                update_data['profile_image'] = filename
                            else:
                                flash('Failed to save profile picture.', 'error')
                                return render_template('admin/user_edit.html', user=user)
                        except Exception as e:
                            flash(f'Error uploading profile picture: {str(e)}', 'error')
                            return render_template('admin/user_edit.html', user=user)
                
                # Update user in database
                mongo_db.db.users.update_one(
                    {'_id': user_object_id},
                    {'$set': update_data}
                )
                
                flash(f'User {full_name} has been updated successfully!', 'success')
                return redirect(url_for('admin.admin_users'))
                
            except Exception as e:
                flash(f'Error updating user: {str(e)}', 'error')
                return render_template('admin/user_edit.html', user=user)
        
        return render_template('admin/user_edit.html', user=user)
    except Exception as e:
        flash(f'Error loading user: {str(e)}', 'error')
        return redirect(url_for('admin.admin_users'))

@mongo_admin_bp.route('/users/<user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_role(user_id):
    """Toggle user role between customer, staff, and sub-admin."""
    try:
        user_data = mongo_db.db.users.find_one({'_id': ObjectId(user_id)})
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        user = MongoUser(user_data)
        
        # Get the role to set from request
        new_role = request.json.get('role', 'customer') if request.is_json else request.form.get('role', 'customer')
        
        # Check permissions based on current user role and requested role
        if current_user.is_admin:
            # Admin can grant any role
            if not current_user.can_grant_roles():
                flash('Access denied. You cannot grant roles.', 'error')
                return redirect(url_for('admin.admin_users'))
        elif current_user.is_sub_admin:
            # Sub-admin can only grant staff role
            if not current_user.can_grant_staff_role():
                flash('Access denied. You cannot grant roles.', 'error')
                return redirect(url_for('admin.admin_users'))
            
            # Sub-admin can only set users to customer or staff
            if new_role not in ['customer', 'staff']:
                flash('Access denied. Sub-admins can only assign Customer or Staff roles.', 'error')
                return redirect(url_for('admin.admin_users'))
        else:
            flash('Access denied. You cannot grant roles.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Cannot modify admin users or self
        if user.is_admin or str(user._id) == str(current_user._id):
            flash('Cannot modify admin users or your own account.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Sub-admins cannot modify other sub-admins
        if current_user.is_sub_admin and user.is_sub_admin:
            flash('Sub-admins cannot modify other sub-admin accounts.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Reset all roles first
        update_data = {
            'is_sub_admin': False,
            'is_staff': False
        }
        
        # Set the new role
        if new_role == 'sub_admin':
            update_data['is_sub_admin'] = True
        elif new_role == 'staff':
            update_data['is_staff'] = True
        # customer role has no special flags (all False)
        
        # Update in database
        mongo_db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        
        role_names = {
            'customer': 'Customer',
            'staff': 'Staff',
            'sub_admin': 'Sub-Admin'
        }
        
        flash(f'User {user.full_name} has been set to {role_names.get(new_role, "Customer")} role.', 'success')
        
    except Exception as e:
        flash(f'Error updating user role: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@mongo_admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_only
def admin_toggle_user_status(user_id):
    """Toggle user active status."""
    try:
        user_data = mongo_db.db.users.find_one({'_id': ObjectId(user_id)})
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        user = MongoUser(user_data)
        
        # Check permissions
        if not current_user.can_manage_users():
            flash('Access denied. You cannot manage users.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Cannot modify admin users or self
        if user.is_admin or str(user._id) == str(current_user._id):
            flash('Cannot modify admin users or your own account.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Cannot deactivate sub-admins unless you're admin
        if user.is_sub_admin and not current_user.is_admin:
            flash('Only admins can modify sub-admin accounts.', 'error')
            return redirect(url_for('admin.admin_users'))
        
        # Toggle active status
        new_active_status = not user.is_active
        
        # Update in database
        mongo_db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_active': new_active_status}}
        )
        
        status_action = 'activated' if new_active_status else 'deactivated'
        flash(f'User {user.full_name} has been {status_action}.', 'success')
        
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@mongo_admin_bp.route('/products')
@login_required
@admin_required
def admin_products():
    """Admin product management page."""
    try:
        products_data = list(mongo_db.db.products.find())
        products = [MongoProduct(product_data) for product_data in products_data]
        return render_template('admin/products.html', products=products)
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    """Add new product page."""
    form = ProductForm()
    
    # Populate category choices
    categories = list(mongo_db.db.categories.find())
    form.category_id.choices = [(str(cat['_id']), cat['name']) for cat in categories]
    
    # Add empty choice if no categories exist
    if not categories:
        form.category_id.choices = [('', 'No categories available')]
        flash('No categories found. Please add categories first.', 'warning')
    
    if form.validate_on_submit():
        try:
            # Validate category_id is not None or empty
            if not form.category_id.data or form.category_id.data == '':
                flash('Please select a valid category.', 'error')
                return render_template('admin/product_form.html', form=form, product=None, title='Add Product')
            
            # Handle image upload
            image_url = None
            if form.image.data and validate_image_file(form.image.data):
                image_url = save_uploaded_file(form.image.data, 'products')
                if not image_url:
                    flash('Failed to upload image. Please try again.', 'error')
                    return render_template('admin/product_form.html', form=form, product=None, title='Add Product')
            elif form.image.data and not validate_image_file(form.image.data):
                flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                return render_template('admin/product_form.html', form=form, product=None, title='Add Product')
            
            # Create new product data
            product_data = {
                'name': form.name.data,
                'name_nepali': form.name_nepali.data,
                'description': form.description.data,
                'price': form.price.data,
                'category_id': ObjectId(form.category_id.data),
                'meat_type': form.meat_type.data,
                'preparation_type': form.preparation_type.data,
                'stock_quantity': form.stock_kg.data,  # Store as stock_quantity in database
                'stock_kg': form.stock_kg.data,        # Also store as stock_kg for compatibility
                'min_order_kg': form.min_order_kg.data,
                'freshness_hours': form.freshness_hours.data,
                'cooking_tips': form.cooking_tips.data,
                'is_featured': form.is_featured.data,
                'date_added': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'is_active': True
            }
            
            # Add image URL if uploaded
            if image_url:
                product_data['image_url'] = image_url
            
            # Insert product into database
            result = mongo_db.db.products.insert_one(product_data)
            
            flash(f'Product "{form.name.data}" has been added successfully!', 'success')
            return redirect(url_for('admin.admin_products'))
            
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('admin/product_form.html', form=form, product=None, title='Add Product')

@mongo_admin_bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    """Edit product page."""
    try:
        # Validate product_id
        if not product_id or product_id == 'None':
            flash('Invalid product ID.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        try:
            product_object_id = ObjectId(product_id)
        except Exception:
            flash('Invalid product ID format.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        product_data = mongo_db.db.products.find_one({'_id': product_object_id})
        if not product_data:
            flash('Product not found.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        product = MongoProduct(product_data)
        form = ProductForm()
        
        # Populate category choices
        categories = list(mongo_db.db.categories.find())
        form.category_id.choices = [(str(cat['_id']), cat['name']) for cat in categories]
        
        # Manually populate form with product data
        if request.method == 'GET':
            form.name.data = product.name
            form.name_nepali.data = product.name_nepali
            form.description.data = product.description
            form.price.data = product.price
            form.category_id.data = str(product.category_id)
            form.meat_type.data = product.meat_type
            form.preparation_type.data = product.preparation_type
            form.stock_kg.data = product.stock_kg  # This uses the property
            form.min_order_kg.data = product.min_order_kg
            form.freshness_hours.data = product.freshness_hours
            form.cooking_tips.data = product.cooking_tips
            form.is_featured.data = product.is_featured
        
        if form.validate_on_submit():
            try:
                # Validate category_id is not None or empty
                if not form.category_id.data or form.category_id.data == '':
                    flash('Please select a valid category.', 'error')
                    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')
                
                # Handle image upload
                new_image_url = None
                if form.image.data and validate_image_file(form.image.data):
                    new_image_url = save_uploaded_file(form.image.data, 'products')
                    if not new_image_url:
                        flash('Failed to upload image. Please try again.', 'error')
                        return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')
                    
                    # Delete old image if it exists
                    if hasattr(product, 'image_url') and product.image_url:
                        delete_file(product.image_url)
                        
                elif form.image.data and not validate_image_file(form.image.data):
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')
                
                # Update product data
                update_data = {
                    'name': form.name.data,
                    'name_nepali': form.name_nepali.data,
                    'description': form.description.data,
                    'price': form.price.data,
                    'category_id': ObjectId(form.category_id.data),
                    'meat_type': form.meat_type.data,
                    'preparation_type': form.preparation_type.data,
                    'stock_quantity': form.stock_kg.data,  # Store as stock_quantity in database
                    'stock_kg': form.stock_kg.data,        # Also store as stock_kg for compatibility
                    'min_order_kg': form.min_order_kg.data,
                    'freshness_hours': form.freshness_hours.data,
                    'cooking_tips': form.cooking_tips.data,
                    'is_featured': form.is_featured.data,
                    'last_updated': datetime.utcnow()
                }
                
                # Update image URL if new image was uploaded
                if new_image_url:
                    update_data['image_url'] = new_image_url
                
                # Update product in database
                result = mongo_db.db.products.update_one(
                    {'_id': product_object_id},
                    {'$set': update_data}
                )
                
                flash(f'Product "{form.name.data}" has been updated successfully!', 'success')
                return redirect(url_for('admin.admin_products'))
                
            except Exception as e:
                flash(f'Error updating product: {str(e)}', 'error')
        

        
        return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')
    except Exception as e:
        flash(f'Error loading product: {str(e)}', 'error')
        return redirect(url_for('admin.admin_products'))

@mongo_admin_bp.route('/products/<product_id>/toggle-featured', methods=['POST'])
@login_required
@admin_required
def admin_toggle_featured(product_id):
    """Toggle product featured status."""
    try:
        # Validate product_id
        if not product_id or product_id == 'None':
            flash('Invalid product ID.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        try:
            product_object_id = ObjectId(product_id)
        except Exception:
            flash('Invalid product ID format.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        product_data = mongo_db.db.products.find_one({'_id': product_object_id})
        if not product_data:
            flash('Product not found.', 'error')
            return redirect(url_for('admin.admin_products'))
        
        product = MongoProduct(product_data)
        new_featured_status = not product.is_featured
        
        # Update in database
        mongo_db.db.products.update_one(
            {'_id': product_object_id},
            {'$set': {'is_featured': new_featured_status, 'last_updated': datetime.utcnow()}}
        )
        
        status_action = 'featured' if new_featured_status else 'unfeatured'
        flash(f'Product {product.name} has been {status_action}.', 'success')
        
    except Exception as e:
        flash(f'Error updating product: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_products'))

@mongo_admin_bp.route('/orders')
@login_required
@staff_required
def admin_orders():
    """Admin order management page."""
    try:
        status_filter = request.args.get('status')
        query = {}
        if status_filter:
            query['status'] = status_filter
        
        orders_data = list(mongo_db.db.orders.find(query).sort('order_date', -1))
        orders = [MongoOrder(order_data) for order_data in orders_data]
        
        return render_template('admin/orders.html', orders=orders, status_filter=status_filter)
    except Exception as e:
        flash(f'Error loading orders: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/orders/<order_id>')
@login_required
@staff_required
def order_detail(order_id):
    """Order detail page."""
    try:
        # Validate order_id
        if not order_id or order_id == 'None':
            flash('Invalid order ID.', 'error')
            return redirect(url_for('admin.admin_orders'))
        
        try:
            order_object_id = ObjectId(order_id)
        except Exception:
            flash('Invalid order ID format.', 'error')
            return redirect(url_for('admin.admin_orders'))
        
        order_data = mongo_db.db.orders.find_one({'_id': order_object_id})
        if not order_data:
            flash('Order not found.', 'error')
            return redirect(url_for('admin.admin_orders'))
        
        order = MongoOrder(order_data)
        
        # Get user details
        user_data = mongo_db.db.users.find_one({'_id': ObjectId(order.user_id)})
        user = MongoUser(user_data) if user_data else None
        
        return render_template('admin/order_detail.html', order=order, user=user)
    except Exception as e:
        flash(f'Error loading order: {str(e)}', 'error')
        return redirect(url_for('admin.admin_orders'))

@mongo_admin_bp.route('/orders/<order_id>/update-status', methods=['POST'])
@login_required
@staff_required
def update_order_status(order_id):
    """Update order status - Admin and Sub-admin only."""
    try:
        # Validate order_id
        if not order_id or order_id == 'None':
            return jsonify({'success': False, 'message': 'Invalid order ID.'}), 400
        
        try:
            order_object_id = ObjectId(order_id)
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid order ID format.'}), 400
        
        # Get new status from request
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'message': 'Status is required.'}), 400
        
        new_status = data['status']
        
        # Validate status
        valid_statuses = ['pending', 'confirmed', 'processing', 'out_for_delivery', 'delivered', 'cod_paid', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status.'}), 400
        
        # Check if order exists
        order_data = mongo_db.db.orders.find_one({'_id': order_object_id})
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
        old_status = order_data.get('status', 'pending')
        
        # Validate status transition
        if not _is_valid_status_transition(old_status, new_status):
            return jsonify({'success': False, 'message': f'Cannot change status from {old_status} to {new_status}.'}), 400
        
        # Update order status
        update_data = {
            'status': new_status,
            'status_updated_at': datetime.now(),
            'status_updated_by': current_user._id
        }
        
        # Add delivery date if status is delivered
        if new_status == 'delivered':
            update_data['delivered_at'] = datetime.now()
            
            # For COD orders, mark as paid when delivered (payment collected during delivery)
            payment_method = order_data.get('payment_method', '').lower().strip()
            current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
            
            if payment_method == 'cod' and current_payment_status != 'paid':
                update_data['payment_status'] = 'paid'
                update_data['payment_confirmed_at'] = datetime.now()
                update_data['payment_confirmed_by'] = current_user._id
                print(f"DEBUG: COD order {order_id} marked as paid upon delivery")
        
        # Auto-mark as paid when status is COD PAID (for COD orders)
        if new_status == 'cod_paid':
            update_data['payment_status'] = 'paid'
            update_data['payment_confirmed_at'] = datetime.now()
            update_data['payment_confirmed_by'] = current_user._id
            print(f"DEBUG: COD payment status updated to 'paid' for order {order_id}")
        
        # Auto-mark as paid when status is confirmed (only for online payments, not COD)
        if new_status == 'confirmed':
            payment_method = order_data.get('payment_method', '').lower().strip()
            current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
            
            # Debug logging
            print(f"DEBUG: Order {order_id} - Payment method: '{payment_method}', Current payment status: '{current_payment_status}'")
            print(f"DEBUG: Condition check - payment_method != 'cod': {payment_method != 'cod'}, current_payment_status != 'paid': {current_payment_status != 'paid'}")
            
            # List of online payment methods
            online_payment_methods = ['esewa', 'khalti', 'ime_pay', 'fonepay']
            
            # Only update payment status for online payments (not COD) and if not already paid
            if (payment_method in online_payment_methods or (payment_method != 'cod' and payment_method != '')) and current_payment_status != 'paid':
                update_data['payment_status'] = 'paid'
                update_data['payment_confirmed_at'] = datetime.now()
                update_data['payment_confirmed_by'] = current_user._id
                print(f"DEBUG: Payment status will be updated to 'paid' for order {order_id}")
            else:
                print(f"DEBUG: Payment status NOT updated for order {order_id} - Reason: payment_method='{payment_method}', current_payment_status='{current_payment_status}'")
        
        result = mongo_db.db.orders.update_one(
            {'_id': order_object_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            # Log status change
            _log_status_change(order_id, old_status, new_status, current_user._id)
            
            # Log payment status change if applicable
            if new_status == 'cod_paid':
                current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
                _log_payment_status_change(order_id, current_payment_status, 'paid', current_user._id, 'cod_paid')
                print(f"DEBUG: COD payment status change logged for order {order_id}")
            elif new_status == 'delivered':
                payment_method = order_data.get('payment_method', '').lower().strip()
                current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
                
                if payment_method == 'cod' and current_payment_status != 'paid':
                    _log_payment_status_change(order_id, current_payment_status, 'paid', current_user._id, 'cod_delivered')
                    print(f"DEBUG: COD payment status change logged for delivered order {order_id}")
            elif new_status == 'confirmed':
                payment_method = order_data.get('payment_method', '').lower().strip()
                current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
                
                print(f"DEBUG: Logging check - payment_method: '{payment_method}', current_payment_status: '{current_payment_status}'")
                
                # List of online payment methods
                online_payment_methods = ['esewa', 'khalti', 'ime_pay', 'fonepay']
                
                if (payment_method in online_payment_methods or (payment_method != 'cod' and payment_method != '')) and current_payment_status != 'paid':
                    _log_payment_status_change(order_id, current_payment_status, 'paid', current_user._id, 'auto_confirmed')
                    print(f"DEBUG: Payment status change logged for order {order_id}")
            
            # Get customer info for notification
            customer_name = 'Customer'
            user_id = order_data.get('user_id')
            if user_id:
                try:
                    user_data = mongo_db.db.users.find_one({'_id': ObjectId(user_id)})
                    customer_name = user_data.get('full_name', 'Customer') if user_data else 'Customer'
                except Exception as e:
                    print(f"Error fetching user data: {e}")
                    customer_name = 'Customer'
            
            # Prepare response message
            message = f'Order status updated to {new_status.replace("_", " ").title()}'
            
            # Add payment status update info if applicable
            if new_status == 'cod_paid':
                message += ' and payment status automatically marked as Paid (COD payment received)'
            elif new_status == 'delivered':
                payment_method = order_data.get('payment_method', '').lower().strip()
                current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
                
                if payment_method == 'cod' and current_payment_status != 'paid':
                    message += ' and payment status automatically marked as Paid (COD payment collected during delivery)'
            elif new_status == 'confirmed':
                payment_method = order_data.get('payment_method', '').lower().strip()
                current_payment_status = order_data.get('payment_status', 'pending').lower().strip()
                
                # List of online payment methods
                online_payment_methods = ['esewa', 'khalti', 'ime_pay', 'fonepay']
                
                if (payment_method in online_payment_methods or (payment_method != 'cod' and payment_method != '')) and current_payment_status != 'paid':
                    message += ' and payment status automatically marked as Paid (online payment)'
            
            return jsonify({
                'success': True, 
                'message': message,
                'old_status': old_status,
                'new_status': new_status,
                'customer_name': customer_name,
                'payment_updated': new_status == 'confirmed' and order_data.get('payment_method', '').lower().strip() in ['esewa', 'khalti', 'ime_pay', 'fonepay'] and order_data.get('payment_status', 'pending').lower().strip() != 'paid'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update order status.'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating order status: {str(e)}'}), 500

@mongo_admin_bp.route('/orders/<order_id>/send-notification', methods=['POST'])
@login_required
@staff_required
def send_order_notification(order_id):
    """Send status update notification to customer."""
    try:
        # Validate order_id
        if not order_id or order_id == 'None':
            return jsonify({'success': False, 'message': 'Invalid order ID.'}), 400
        
        try:
            order_object_id = ObjectId(order_id)
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid order ID format.'}), 400
        
        # Get order and customer details
        order_data = mongo_db.db.orders.find_one({'_id': order_object_id})
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
        user_id = order_data.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Order has no associated customer.'}), 400
            
        try:
            user_data = mongo_db.db.users.find_one({'_id': ObjectId(user_id)})
            if not user_data:
                return jsonify({'success': False, 'message': 'Customer not found.'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error fetching customer data: {str(e)}'}), 500
        
        order = MongoOrder(order_data)
        customer = MongoUser(user_data)
        
        # Get notification message from request or use default
        data = request.get_json() or {}
        custom_message = data.get('message', '')
        
        # Create notification message
        status_messages = {
            'confirmed': 'Your order has been confirmed and is being prepared.',
            'processing': 'Your order is currently being processed.',
            'out_for_delivery': 'Great news! Your order is out for delivery.',
            'delivered': 'Your order has been delivered successfully.',
            'cod_paid': 'Thank you! Your COD payment has been received and your order is complete.',
            'cancelled': 'Your order has been cancelled.'
        }
        
        if custom_message:
            notification_message = custom_message
        else:
            notification_message = status_messages.get(order.status, f'Your order status has been updated to {order.status.replace("_", " ").title()}.')
        
        # In a real application, you would send email/SMS here
        # For now, we'll just log the notification
        notification_data = {
            'order_id': order_id,
            'customer_id': str(customer._id),
            'customer_email': customer.email,
            'message': notification_message,
            'status': order.status,
            'sent_at': datetime.now(),
            'sent_by': current_user._id,
            'type': 'status_update'
        }
        
        # Store notification in database
        mongo_db.db.notifications.insert_one(notification_data)
        
        return jsonify({
            'success': True,
            'message': f'Notification sent to {customer.full_name}',
            'customer_email': customer.email,
            'notification_message': notification_message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending notification: {str(e)}'}), 500

def _is_valid_status_transition(old_status, new_status):
    """Validate if status transition is allowed."""
    # Define valid transitions
    transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['processing', 'cancelled'],
        'processing': ['out_for_delivery', 'cancelled'],
        'out_for_delivery': ['delivered', 'cod_paid', 'cancelled'],
        'delivered': [],  # Final status - no transitions allowed from delivered
        'cod_paid': [],  # Final status for COD orders
        'cancelled': []   # Final status
    }
    
    return new_status in transitions.get(old_status, [])

def _log_status_change(order_id, old_status, new_status, admin_id):
    """Log order status changes for audit trail."""
    log_data = {
        'order_id': order_id,
        'old_status': old_status,
        'new_status': new_status,
        'changed_by': admin_id,
        'changed_at': datetime.now(),
        'type': 'status_change'
    }
    
    mongo_db.db.order_logs.insert_one(log_data)

def _log_payment_status_change(order_id, old_payment_status, new_payment_status, admin_id, trigger_type='manual'):
    """Log payment status changes for audit trail."""
    log_data = {
        'order_id': order_id,
        'old_payment_status': old_payment_status,
        'new_payment_status': new_payment_status,
        'changed_by': admin_id,
        'changed_at': datetime.now(),
        'trigger_type': trigger_type,  # 'manual', 'auto_confirmed', 'webhook'
        'type': 'payment_status_change'
    }
    
    mongo_db.db.order_logs.insert_one(log_data)

@mongo_admin_bp.route('/export/users')
@login_required
@admin_required
def export_users():
    """Export users data as CSV."""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Get all users
        users_data = list(mongo_db.db.users.find())
        users = [MongoUser(user_data) for user_data in users_data]
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Full Name', 'Email', 'Phone', 'Role', 'Status', 
            'Date Joined', 'Last Login', 'Total Orders'
        ])
        
        # Write user data
        for user in users:
            role = 'Admin' if user.is_admin else ('Sub-admin' if user.is_sub_admin else 'Customer')
            status = 'Active' if user.is_active else 'Inactive'
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
            date_joined = user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else 'N/A'
            
            writer.writerow([
                str(user._id), user.full_name, user.email, user.phone or 'N/A',
                role, status, date_joined, last_login, len(user.orders)
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting users: {str(e)}', 'error')
        return redirect(url_for('admin.admin_users'))

@mongo_admin_bp.route('/export/users/pdf')
@login_required
@admin_required
def export_users_pdf():
    """Export users data as PDF."""
    try:
        from flask import make_response
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get all users
        users_data = list(mongo_db.db.users.find())
        users = [MongoUser(user_data) for user_data in users_data]
        
        # Create PDF content
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        # Add title
        title = Paragraph("Nepal Meat Shop - Users Export Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add export info
        export_info = f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        export_info += f" | Total Users: {len(users)}"
        
        # Add user statistics
        active_users = len([u for u in users if u.is_active])
        admin_users = len([u for u in users if u.is_admin])
        sub_admin_users = len([u for u in users if u.is_sub_admin])
        staff_users = len([u for u in users if u.is_staff])
        customer_users = len([u for u in users if not u.is_admin and not u.is_sub_admin and not u.is_staff])
        inactive_users = len([u for u in users if not u.is_active])
        
        export_info += f" | Active: {active_users} | Admins: {admin_users} | Sub-Admins: {sub_admin_users} | Staff: {staff_users} | Customers: {customer_users} | Inactive: {inactive_users}"
        
        info_para = Paragraph(export_info, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        # Prepare table data
        data = [['Full Name', 'Email', 'Phone', 'Role', 'Status', 'Date Joined', 'Last Login', 'Orders']]
        
        for user in users:
            # Determine role
            if user.is_admin:
                role = 'Admin'
            elif user.is_sub_admin:
                role = 'Sub-Admin'
            elif user.is_staff:
                role = 'Staff'
            else:
                role = 'Customer'
            
            status = 'Active' if user.is_active else 'Inactive'
            last_login = user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
            date_joined = user.date_joined.strftime('%Y-%m-%d') if user.date_joined else 'N/A'
            
            # Truncate long text for better table formatting
            full_name = user.full_name[:20] + '...' if len(user.full_name) > 20 else user.full_name
            email = user.email[:25] + '...' if len(user.email) > 25 else user.email
            phone = user.phone[:15] if user.phone else 'N/A'
            
            data.append([
                full_name,
                email,
                phone,
                role,
                status,
                date_joined,
                last_login,
                str(len(user.orders))
            ])
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1*inch, 0.8*inch, 0.7*inch, 0.9*inch, 0.9*inch, 0.6*inch])
        
        # Add style to table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Create response
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting users: {str(e)}', 'error')
        return redirect(url_for('admin.admin_users'))

@mongo_admin_bp.route('/export/orders')
@login_required
@staff_required
def export_orders():
    """Export orders data as PDF."""
    try:
        from flask import make_response
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get filter parameters
        status_filter = request.args.get('status')
        query = {}
        if status_filter:
            query['status'] = status_filter
        
        # Get all orders
        orders_data = list(mongo_db.db.orders.find(query).sort('order_date', -1))
        orders = [MongoOrder(order_data) for order_data in orders_data]
        
        # Create PDF content
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        # Add title
        title = Paragraph("Nepal Meat Shop - Orders Export Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add export info
        export_info = f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if status_filter:
            export_info += f" | Status Filter: {status_filter.title()}"
        export_info += f" | Total Orders: {len(orders)}"
        
        info_para = Paragraph(export_info, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        # Prepare table data
        data = [['Order ID', 'Customer', 'Email', 'Date', 'Status', 'Amount', 'Items', 'Address']]
        
        for order in orders:
            # Get customer details
            user_data = mongo_db.db.users.find_one({'_id': ObjectId(order.user_id)})
            customer_name = user_data.get('full_name', 'N/A') if user_data else 'N/A'
            customer_email = user_data.get('email', 'N/A') if user_data else 'N/A'
            
            order_date = order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A'
            
            # Handle delivery_address - it can be a dict or string
            if order.delivery_address:
                if isinstance(order.delivery_address, dict):
                    delivery_address = f"{order.delivery_address.get('street', '')}, {order.delivery_address.get('city', '')}"
                else:
                    delivery_address = str(order.delivery_address)
            else:
                delivery_address = 'N/A'
            
            # Truncate long text for better table formatting
            customer_name = customer_name[:15] + '...' if len(customer_name) > 15 else customer_name
            customer_email = customer_email[:20] + '...' if len(customer_email) > 20 else customer_email
            delivery_address = delivery_address[:25] + '...' if len(delivery_address) > 25 else delivery_address
            
            data.append([
                str(order._id)[:8] + '...',  # Truncate order ID
                customer_name,
                customer_email,
                order_date,
                order.status.title(),
                f"Rs. {order.total_amount:.0f}",
                str(len(order.items)),
                delivery_address
            ])
        
        # Create table
        table = Table(data, colWidths=[0.8*inch, 1.2*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.5*inch, 1.7*inch])
        
        # Add style to table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Create response
        filename_suffix = f"_{status_filter}" if status_filter else ""
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=orders_export{filename_suffix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting orders: {str(e)}', 'error')
        return redirect(url_for('admin.admin_orders'))

@mongo_admin_bp.route('/export/orders/csv')
@login_required
@staff_required
def export_orders_csv():
    """Export orders data as CSV."""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Get filter parameters
        status_filter = request.args.get('status')
        query = {}
        if status_filter:
            query['status'] = status_filter
        
        # Get all orders
        orders_data = list(mongo_db.db.orders.find(query).sort('order_date', -1))
        orders = [MongoOrder(order_data) for order_data in orders_data]
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order ID', 'Customer Name', 'Customer Email', 'Order Date', 
            'Status', 'Total Amount', 'Items Count', 'Delivery Address'
        ])
        
        # Write order data
        for order in orders:
            # Get customer details
            user_data = mongo_db.db.users.find_one({'_id': ObjectId(order.user_id)})
            customer_name = user_data.get('full_name', 'N/A') if user_data else 'N/A'
            customer_email = user_data.get('email', 'N/A') if user_data else 'N/A'
            
            order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else 'N/A'
            
            # Handle delivery_address - it can be a dict or string
            if order.delivery_address:
                if isinstance(order.delivery_address, dict):
                    delivery_address = f"{order.delivery_address.get('street', '')}, {order.delivery_address.get('city', '')}"
                else:
                    delivery_address = str(order.delivery_address)
            else:
                delivery_address = 'N/A'
            
            writer.writerow([
                str(order._id), customer_name, customer_email, order_date,
                order.status.title(), f"Rs. {order.total_amount:.2f}", 
                len(order.items), delivery_address
            ])
        
        # Create response
        filename_suffix = f"_{status_filter}" if status_filter else ""
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=orders_export{filename_suffix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting orders: {str(e)}', 'error')
        return redirect(url_for('admin.admin_orders'))

@mongo_admin_bp.route('/download-orders-pdf', methods=['POST'])
@login_required
@staff_required
def download_orders_pdf():
    """Download selected orders as PDF."""
    try:
        from flask import make_response
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get order IDs from form data
        order_ids = request.form.getlist('order_ids')
        export_all = request.form.get('export_all', 'false').lower() == 'true'
        
        if not order_ids and not export_all:
            flash('No orders selected for download.', 'error')
            return redirect(url_for('admin.business_insights'))
        
        # If export_all is true, get all orders
        if export_all:
            orders_data = list(mongo_db.db.orders.find().sort('order_date', -1))
            orders = [MongoOrder(order_data) for order_data in orders_data]
        else:
            # Convert string IDs to ObjectIds
            object_ids = []
            for order_id in order_ids:
                try:
                    object_ids.append(ObjectId(order_id))
                except Exception:
                    continue
            
            if not object_ids:
                flash('Invalid order IDs provided.', 'error')
                return redirect(url_for('admin.business_insights'))
            
            # Get selected orders
            orders_data = list(mongo_db.db.orders.find({'_id': {'$in': object_ids}}).sort('order_date', -1))
            orders = [MongoOrder(order_data) for order_data in orders_data]
        
        # Create PDF content
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        # Add title
        report_type = "All Orders Report" if export_all else "Selected Orders Report"
        title = Paragraph(f"Nepal Meat Shop - {report_type}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add export info
        export_info = f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        order_count_label = "Total Orders" if export_all else "Selected Orders"
        export_info += f" | {order_count_label}: {len(orders)}"
        
        info_para = Paragraph(export_info, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        # Prepare table data
        data = [['Order ID', 'Customer', 'Email', 'Date', 'Status', 'Amount', 'Items', 'Address']]
        
        for order in orders:
            # Get customer details
            user_data = mongo_db.db.users.find_one({'_id': ObjectId(order.user_id)})
            customer_name = user_data.get('full_name', 'N/A') if user_data else 'N/A'
            customer_email = user_data.get('email', 'N/A') if user_data else 'N/A'
            
            order_date = order.order_date.strftime('%Y-%m-%d') if order.order_date else 'N/A'
            
            # Handle delivery_address - it can be a dict or string
            if order.delivery_address:
                if isinstance(order.delivery_address, dict):
                    delivery_address = f"{order.delivery_address.get('street', '')}, {order.delivery_address.get('city', '')}"
                else:
                    delivery_address = str(order.delivery_address)
            else:
                delivery_address = 'N/A'
            
            # Truncate long text for better table formatting
            customer_name = customer_name[:15] + '...' if len(customer_name) > 15 else customer_name
            customer_email = customer_email[:20] + '...' if len(customer_email) > 20 else customer_email
            delivery_address = delivery_address[:25] + '...' if len(delivery_address) > 25 else delivery_address
            
            data.append([
                str(order._id)[:8] + '...',  # Truncate order ID
                customer_name,
                customer_email,
                order_date,
                order.status.title(),
                f"Rs. {order.total_amount:.0f}",
                str(len(order.items)),
                delivery_address
            ])
        
        # Create table
        table = Table(data, colWidths=[0.8*inch, 1.2*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.5*inch, 1.7*inch])
        
        # Add style to table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Create response
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        filename_prefix = "all_orders" if export_all else "selected_orders"
        response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Error downloading orders: {str(e)}', 'error')
        return redirect(url_for('admin.business_insights'))

@mongo_admin_bp.route('/download-orders-csv', methods=['POST'])
@login_required
@staff_required
def download_orders_csv():
    """Download selected orders as CSV."""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Get order IDs from form data
        order_ids = request.form.getlist('order_ids')
        export_all = request.form.get('export_all', 'false').lower() == 'true'
        
        if not order_ids and not export_all:
            flash('No orders selected for download.', 'error')
            return redirect(url_for('admin.business_insights'))
        
        # If export_all is true, get all orders
        if export_all:
            orders_data = list(mongo_db.db.orders.find().sort('order_date', -1))
            orders = [MongoOrder(order_data) for order_data in orders_data]
        else:
            # Convert string IDs to ObjectIds
            object_ids = []
            for order_id in order_ids:
                try:
                    object_ids.append(ObjectId(order_id))
                except Exception:
                    continue
            
            if not object_ids:
                flash('Invalid order IDs provided.', 'error')
                return redirect(url_for('admin.business_insights'))
            
            # Get selected orders
            orders_data = list(mongo_db.db.orders.find({'_id': {'$in': object_ids}}).sort('order_date', -1))
            orders = [MongoOrder(order_data) for order_data in orders_data]
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order ID', 'Customer Name', 'Customer Email', 'Order Date', 
            'Status', 'Total Amount', 'Items Count', 'Delivery Address'
        ])
        
        # Write order data
        for order in orders:
            # Get customer details
            user_data = mongo_db.db.users.find_one({'_id': ObjectId(order.user_id)})
            customer_name = user_data.get('full_name', 'N/A') if user_data else 'N/A'
            customer_email = user_data.get('email', 'N/A') if user_data else 'N/A'
            
            order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else 'N/A'
            
            # Handle delivery_address - it can be a dict or string
            if order.delivery_address:
                if isinstance(order.delivery_address, dict):
                    delivery_address = f"{order.delivery_address.get('street', '')}, {order.delivery_address.get('city', '')}"
                else:
                    delivery_address = str(order.delivery_address)
            else:
                delivery_address = 'N/A'
            
            writer.writerow([
                str(order._id), customer_name, customer_email, order_date,
                order.status.title(), f"Rs. {order.total_amount:.2f}", 
                len(order.items), delivery_address
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        filename_prefix = "all_orders" if export_all else "selected_orders"
        response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error downloading orders: {str(e)}', 'error')
        return redirect(url_for('admin.business_insights'))

# Category Management Routes
@mongo_admin_bp.route('/categories')
@login_required
@admin_required
def admin_categories():
    """Admin category management page."""
    try:
        categories_data = list(mongo_db.db.categories.find().sort('name', 1))
        categories = []
        
        for cat in categories_data:
            # Validate that the category has a valid _id
            if '_id' not in cat or cat['_id'] is None:
                print(f"Warning: Found category without valid _id: {cat}")
                continue
                
            try:
                # Ensure _id can be converted to string
                category_id = str(cat['_id'])
                if not category_id or category_id == 'None':
                    print(f"Warning: Found category with invalid _id: {cat['_id']}")
                    continue
                    
                categories.append({
                    '_id': category_id,
                    'name': cat.get('name', 'Unnamed Category'),
                    'name_nepali': cat.get('name_nepali', ''),
                    'description': cat.get('description', '')
                })
            except Exception as e:
                print(f"Error processing category {cat}: {str(e)}")
                continue
                
        return render_template('admin/categories.html', categories=categories)
    except Exception as e:
        flash(f'Error loading categories: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_category():
    """Add new category."""
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            category_data = {
                'name': form.name.data,
                'name_nepali': form.name_nepali.data,
                'description': form.description.data,
                'is_active': True,
                'sort_order': 0,
                'date_added': datetime.utcnow()
            }
            
            # Insert category into database
            result = mongo_db.db.categories.insert_one(category_data)
            
            flash(f'Category "{form.name.data}" has been added successfully!', 'success')
            return redirect(url_for('admin.admin_categories'))
        except Exception as e:
            flash(f'Error adding category: {str(e)}', 'error')
            return redirect(url_for('admin.admin_categories'))


@mongo_admin_bp.route('/payment-gateways')
@login_required
@admin_required
def admin_payment_gateways():
    """Payment gateway management page."""
    try:
        return render_template('admin/payment_gateways.html', title='Payment Gateway Management')
    except Exception as e:
        flash(f'Error loading payment gateways: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@mongo_admin_bp.route('/business-insights')
@mongo_admin_bp.route('/business_insights')
@login_required
@admin_required
def business_insights():
    """Business insights dashboard for admins and sub-admins only."""
    try:
        from app.utils.analytics import BusinessAnalytics
        
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        sort_reviews = request.args.get('sort_reviews', 'date')
        
        # Parse dates if provided
        date_range = {}
        if date_from:
            try:
                date_range['start'] = datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                pass
        if date_to:
            try:
                date_range['end'] = datetime.strptime(date_to, '%Y-%m-%d')
            except ValueError:
                pass
        
        # Get analytics data
        delivery_stats = BusinessAnalytics.get_delivery_statistics(
            start_date=date_range.get('start') if date_range else None,
            end_date=date_range.get('end') if date_range else None
        )
        filtered_orders = BusinessAnalytics.get_filtered_orders(
            status_filter=status_filter,
            start_date=date_range.get('start') if date_range else None,
            end_date=date_range.get('end') if date_range else None
        )
        customer_reviews = BusinessAnalytics.get_customer_reviews(sort_by=sort_reviews)
        financial_summary = BusinessAnalytics.get_financial_summary(
            start_date=date_range.get('start') if date_range else None,
            end_date=date_range.get('end') if date_range else None
        )
        monthly_trends_data = BusinessAnalytics.get_monthly_revenue_trends()
        
        return render_template('admin/business_insights.html',
                             delivery_stats=delivery_stats,
                             filtered_orders=filtered_orders,
                             customer_reviews=customer_reviews,
                             financial_summary=financial_summary,
                             monthly_trends=monthly_trends_data,
                             status_filter=status_filter,
                             date_from=date_from,
                             date_to=date_to,
                             sort_reviews=sort_reviews,
                             title='Business Insights Dashboard')
    
    except Exception as e:
        flash(f'Error loading business insights: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/business-insights/download-pdf')
@login_required
@admin_required
def download_business_insights_pdf():
    """Download business insights as PDF report."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        from flask import make_response
        from app.utils.analytics import BusinessAnalytics
        
        # Get analytics data
        delivery_stats = BusinessAnalytics.get_delivery_statistics()
        financial_summary = BusinessAnalytics.get_financial_summary()
        monthly_trends_data = BusinessAnalytics.get_monthly_revenue_trends()
        monthly_trends = monthly_trends_data.get('trends', []) if monthly_trends_data else []
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#667eea')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Add title
        title = Paragraph("🍖 Nepal Meat Shop - Business Insights Report", title_style)
        elements.append(title)
        
        # Add generation date
        from datetime import datetime
        date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 20))
        
        # Delivery Statistics Section
        delivery_heading = Paragraph("📊 Delivery Statistics", heading_style)
        elements.append(delivery_heading)
        
        delivery_data = [
            ['Metric', 'Value'],
            ['Total Orders', str(delivery_stats.get('total_orders', 0))],
            ['Successful Deliveries', str(delivery_stats.get('successful_deliveries', 0))],
            ['Cancelled Orders', str(delivery_stats.get('canceled_orders', 0))],
            ['Pending Orders', str(delivery_stats.get('pending_orders', 0))],
            ['Success Rate', f"{delivery_stats.get('success_rate', 0):.1f}%"],
            ['Cancellation Rate', f"{delivery_stats.get('cancellation_rate', 0):.1f}%"]
        ]
        
        delivery_table = Table(delivery_data, colWidths=[3*inch, 2*inch])
        delivery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(delivery_table)
        elements.append(Spacer(1, 20))
        
        # Financial Summary Section
        financial_heading = Paragraph("💰 Financial Summary", heading_style)
        elements.append(financial_heading)
        
        financial_data = [
            ['Metric', 'Value'],
            ['Total Revenue', f"Rs. {financial_summary.get('total_revenue', 0):,.0f}"],
            ['Total Orders', str(financial_summary.get('total_orders', 0))],
            ['Average Order Value', f"Rs. {financial_summary.get('average_order_value', 0):,.0f}"]
        ]
        
        financial_table = Table(financial_data, colWidths=[3*inch, 2*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(financial_table)
        elements.append(Spacer(1, 20))
        
        # Top Delivery Areas Section
        if financial_summary.get('top_delivery_areas'):
            areas_heading = Paragraph("🚚 Top Delivery Areas", heading_style)
            elements.append(areas_heading)
            
            areas_data = [['Area', 'Orders', 'Revenue']]
            for area in financial_summary.get('top_delivery_areas', [])[:5]:
                areas_data.append([
                    area.get('area', 'Unknown'),
                    str(area.get('order_count', 0)),
                    f"Rs. {area.get('revenue', 0):,.0f}"
                ])
            
            areas_table = Table(areas_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            areas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(areas_table)
            elements.append(Spacer(1, 20))
        
        # Monthly Revenue Trends Section
        if monthly_trends:
            trends_heading = Paragraph("📈 Monthly Revenue Trends", heading_style)
            elements.append(trends_heading)
            
            trends_data = [['Month', 'Revenue', 'Orders', 'Avg Order Value']]
            for trend in monthly_trends[-6:]:  # Last 6 months
                trends_data.append([
                    trend.get('month', 'Unknown'),
                    f"Rs. {trend.get('revenue', 0):,.0f}",
                    str(trend.get('orders', 0)),
                    f"Rs. {trend.get('average_order_value', 0):,.0f}"
                ])
            
            trends_table = Table(trends_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
            trends_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(trends_table)
        
        # Add footer
        elements.append(Spacer(1, 30))
        footer_text = Paragraph(
            "This report was generated automatically by Nepal Meat Shop Business Intelligence System.",
            styles['Normal']
        )
        elements.append(footer_text)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=business-insights-report-{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except ImportError:
        flash('PDF generation requires reportlab library. Please install it: pip install reportlab', 'error')
        return redirect(url_for('admin.business_insights'))
    except Exception as e:
        flash(f'Error generating PDF report: {str(e)}', 'error')
        return redirect(url_for('admin.business_insights'))

# QR Code Management Routes
@mongo_admin_bp.route('/qr-codes')
@login_required
@admin_only
def admin_qr_codes():
    """Admin QR code management page."""
    try:
        # Get all QR codes from database
        qr_codes_data = []
        if mongo_db.db is not None:
            qr_codes_data = list(mongo_db.db.qr_codes.find().sort('payment_method', 1))
        else:
            # Fallback data when MongoDB is not available
            print("MongoDB not available, using fallback QR code data for admin")
            qr_codes_data = [
                {
                    'payment_method': 'bank',
                    'qr_image': 'qr_codes/bank_transfer_qr_code.svg',
                    'description': 'Bank Transfer QR Code for payments',
                    'display_name': 'Bank Transfer',
                    'last_updated': None
                },
                {
                    'payment_method': 'esewa',
                    'qr_image': 'qr_codes/esewa_qr_code.svg',
                    'description': 'Pay using eSewa digital wallet',
                    'display_name': 'eSewa',
                    'last_updated': None
                },
                {
                    'payment_method': 'khalti',
                    'qr_image': 'qr_codes/khalti_qr_code.svg',
                    'description': 'Pay using Khalti digital wallet',
                    'display_name': 'Khalti',
                    'last_updated': None
                },
                {
                    'payment_method': 'ime_pay',
                    'qr_image': 'qr_codes/ime_pay_qr_code.svg',
                    'description': 'Pay using IME Pay digital wallet',
                    'display_name': 'IME Pay',
                    'last_updated': None
                },
                {
                    'payment_method': 'fonepay',
                    'qr_image': 'qr_codes/fone_pay_qr_code.svg',
                    'description': 'Pay using FonePay digital wallet',
                    'display_name': 'FonePay',
                    'last_updated': None
                },
                {
                    'payment_method': 'prabhupay',
                    'qr_image': 'qr_codes/prabhu_pay_qr_code.svg',
                    'description': 'Pay using PrabhuPay digital wallet',
                    'display_name': 'PrabhuPay',
                    'last_updated': None
                },
                {
                    'payment_method': 'cellpay',
                    'qr_image': 'qr_codes/cell_pay_qr_code.svg',
                    'description': 'Pay using CellPay digital wallet',
                    'display_name': 'CellPay',
                    'last_updated': None
                }
            ]
        
        # Define available payment methods
        available_methods = [
            {'id': 'bank', 'name': 'Bank Transfer', 'name_nepali': 'बैंक ट्रान्सफर'},
            {'id': 'esewa', 'name': 'eSewa', 'name_nepali': 'ईसेवा'},
            {'id': 'khalti', 'name': 'Khalti', 'name_nepali': 'खल्ती'},
            {'id': 'ime_pay', 'name': 'IME Pay', 'name_nepali': 'आईएमई पे'},
            {'id': 'fonepay', 'name': 'FonePay', 'name_nepali': 'फोनपे'},
            {'id': 'prabhupay', 'name': 'PrabhuPay', 'name_nepali': 'प्रभुपे'},
            {'id': 'cellpay', 'name': 'CellPay', 'name_nepali': 'सेलपे'},
        ]
        
        # Create a map of existing QR codes
        existing_qr_codes = {qr['payment_method']: qr for qr in qr_codes_data}
        
        return render_template('admin/qr_codes.html', 
                             qr_codes=existing_qr_codes, 
                             available_methods=available_methods)
    except Exception as e:
        flash(f'Error loading QR codes: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@mongo_admin_bp.route('/qr-codes/<payment_method>/upload', methods=['GET', 'POST'])
@login_required
@admin_only
def admin_upload_qr_code(payment_method):
    """Upload QR code for a payment method."""
    try:
        # Validate payment method
        valid_methods = ['bank', 'esewa', 'khalti', 'ime_pay', 'fonepay', 'prabhupay', 'cellpay']
        if payment_method not in valid_methods:
            flash('Invalid payment method.', 'error')
            return redirect(url_for('admin.admin_qr_codes'))
        
        form = QRCodeForm()
        form.payment_method.data = payment_method
        
        if form.validate_on_submit():
            try:
                # Validate image file
                if not validate_image_file(form.qr_image.data):
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                    return render_template('admin/qr_code_form.html', form=form, 
                                         title=f'Upload QR Code - {payment_method.title()}')
                
                # Save QR code image
                filename = save_uploaded_file(form.qr_image.data, 'qr_codes')
                if not filename:
                    flash('Failed to save QR code image.', 'error')
                    return render_template('admin/qr_code_form.html', form=form, 
                                         title=f'Upload QR Code - {payment_method.title()}')
                
                # Check if QR code already exists for this payment method
                existing_qr = None
                if mongo_db.db is not None:
                    existing_qr = mongo_db.db.qr_codes.find_one({'payment_method': payment_method})
                
                if mongo_db.db is not None:
                    if existing_qr:
                        # Delete old QR code image
                        if existing_qr.get('qr_image'):
                            delete_file(existing_qr['qr_image'])
                        
                        # Update existing QR code
                        mongo_db.db.qr_codes.update_one(
                            {'payment_method': payment_method},
                            {'$set': {
                                'qr_image': filename,
                                'description': form.description.data,
                                'last_updated': datetime.utcnow(),
                                'updated_by': str(current_user._id)
                            }}
                        )
                        flash(f'QR code for {payment_method.title()} has been updated successfully!', 'success')
                    else:
                        # Create new QR code entry
                        qr_code_data = {
                            'payment_method': payment_method,
                            'qr_image': filename,
                            'description': form.description.data,
                            'is_active': True,
                            'date_added': datetime.utcnow(),
                            'added_by': str(current_user._id)
                        }
                        mongo_db.db.qr_codes.insert_one(qr_code_data)
                        flash(f'QR code for {payment_method.title()} has been uploaded successfully!', 'success')
                else:
                    print(f"MongoDB not available, skipping QR code upload for {payment_method}")
                    flash(f'QR code for {payment_method.title()} has been uploaded successfully! (Note: Database not available)', 'success')
                
                return redirect(url_for('admin.admin_qr_codes'))
                
            except Exception as e:
                flash(f'Error uploading QR code: {str(e)}', 'error')
        
        return render_template('admin/qr_code_form.html', form=form, 
                             title=f'Upload QR Code - {payment_method.title()}')
    except Exception as e:
        flash(f'Error loading QR code form: {str(e)}', 'error')
        return redirect(url_for('admin.admin_qr_codes'))

@mongo_admin_bp.route('/qr-codes/<payment_method>/edit', methods=['GET', 'POST'])
@login_required
@admin_only
def admin_edit_qr_code(payment_method):
    """Edit QR code for a payment method."""
    try:
        # Validate payment method
        valid_methods = ['bank', 'esewa', 'khalti', 'ime_pay', 'fonepay', 'prabhupay', 'cellpay']
        if payment_method not in valid_methods:
            flash('Invalid payment method.', 'error')
            return redirect(url_for('admin.admin_qr_codes'))
        
        # Get existing QR code
        qr_code_data = None
        if mongo_db.db is not None:
            qr_code_data = mongo_db.db.qr_codes.find_one({'payment_method': payment_method})
        else:
            # Fallback data when MongoDB is not available
            fallback_qr_codes = {
                'bank': {
                    'payment_method': 'bank',
                    'qr_image': 'qr_codes/bank_transfer_qr_code.svg',
                    'description': 'Bank Transfer QR Code for payments',
                    'display_name': 'Bank Transfer',
                    'last_updated': None
                },
                'esewa': {
                    'payment_method': 'esewa',
                    'qr_image': 'qr_codes/steamed-momos-wontons-1957616-hero-01-1c59e22bad0347daa8f0dfe12894bc3c_20250807_190551_0833350d.jpg',
                    'description': 'Pay using eSewa digital wallet',
                    'display_name': 'eSewa',
                    'last_updated': None
                },
                'khalti': {
                    'payment_method': 'khalti',
                    'qr_image': 'qr_codes/steamed-momos-wontons-1957616-hero-01-1c59e22bad0347daa8f0dfe12894bc3c_20250807_190551_0833350d.jpg',
                    'description': 'Pay using Khalti digital wallet',
                    'display_name': 'Khalti',
                    'last_updated': None
                }
            }
            qr_code_data = fallback_qr_codes.get(payment_method)
        
        if not qr_code_data:
            flash('QR code not found.', 'error')
            return redirect(url_for('admin.admin_qr_codes'))
        
        form = QRCodeUpdateForm()
        form.payment_method.data = payment_method
        
        if form.validate_on_submit():
            try:
                update_data = {
                    'description': form.description.data,
                    'last_updated': datetime.utcnow(),
                    'updated_by': str(current_user._id)
                }
                
                # Handle new QR code image upload
                if form.qr_image.data and form.qr_image.data.filename:
                    # Validate image file
                    if not validate_image_file(form.qr_image.data):
                        flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                        payment_method_display = payment_method.replace('_', ' ').title()
                        return render_template('admin/edit_qr_code.html', form=form, 
                                             qr_code=qr_code_data, 
                                             payment_method_display=payment_method_display,
                                             title=f'Edit QR Code - {payment_method.title()}')
                    
                    # Delete old QR code image
                    if qr_code_data.get('qr_image'):
                        delete_file(qr_code_data['qr_image'])
                    
                    # Save new QR code image
                    filename = save_uploaded_file(form.qr_image.data, 'qr_codes')
                    if filename:
                        update_data['qr_image'] = filename
                    else:
                        flash('Failed to save new QR code image.', 'error')
                        payment_method_display = payment_method.replace('_', ' ').title()
                        return render_template('admin/edit_qr_code.html', form=form, 
                                             qr_code=qr_code_data, 
                                             payment_method_display=payment_method_display,
                                             title=f'Edit QR Code - {payment_method.title()}')
                
                # Update QR code in database
                if mongo_db.db is not None:
                    mongo_db.db.qr_codes.update_one(
                        {'payment_method': payment_method},
                        {'$set': update_data}
                    )
                else:
                    print(f"MongoDB not available, skipping QR code update for {payment_method}")
                
                flash(f'QR code for {payment_method.title()} has been updated successfully!', 'success')
                return redirect(url_for('admin.admin_qr_codes'))
                
            except Exception as e:
                flash(f'Error updating QR code: {str(e)}', 'error')
        
        # Pre-populate form with existing data
        if request.method == 'GET':
            form.description.data = qr_code_data.get('description', '')
        
        # Create payment method display name
        payment_method_display = payment_method.replace('_', ' ').title()
        
        return render_template('admin/edit_qr_code.html', form=form, 
                             qr_code=qr_code_data, 
                             payment_method_display=payment_method_display,
                             title=f'Edit QR Code - {payment_method.title()}')
    except Exception as e:
        flash(f'Error loading QR code: {str(e)}', 'error')
        return redirect(url_for('admin.admin_qr_codes'))



@mongo_admin_bp.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_category(category_id):
    """Edit category."""
    try:
        # Validate category_id
        if not category_id or category_id == 'None':
            flash('Invalid category ID.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        try:
            category_object_id = ObjectId(category_id)
        except Exception:
            flash('Invalid category ID format.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        category_data = mongo_db.db.categories.find_one({'_id': category_object_id})
        if not category_data:
            flash('Category not found.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        form = CategoryForm()
        
        if form.validate_on_submit():
            try:
                update_data = {
                    'name': form.name.data,
                    'name_nepali': form.name_nepali.data,
                    'description': form.description.data,
                    'last_updated': datetime.utcnow()
                }
                
                # Update category in database
                mongo_db.db.categories.update_one(
                    {'_id': category_object_id},
                    {'$set': update_data}
                )
                
                flash(f'Category "{form.name.data}" has been updated successfully!', 'success')
                return redirect(url_for('admin.admin_categories'))
                
            except Exception as e:
                flash(f'Error updating category: {str(e)}', 'error')
        
        # Pre-populate form with existing data
        if request.method == 'GET':
            form.name.data = category_data.get('name', '')
            form.name_nepali.data = category_data.get('name_nepali', '')
            form.description.data = category_data.get('description', '')
        
        return render_template('admin/category_form.html', form=form, title='Edit Category')
    except Exception as e:
        flash(f'Error loading category: {str(e)}', 'error')
        return redirect(url_for('admin.admin_categories'))

@mongo_admin_bp.route('/categories/<category_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    """Delete category."""
    try:
        # Validate category_id
        if not category_id or category_id == 'None':
            flash('Invalid category ID.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        try:
            category_object_id = ObjectId(category_id)
        except Exception:
            flash('Invalid category ID format.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        # Check if category has products
        products_count = mongo_db.db.products.count_documents({'category_id': category_object_id})
        if products_count > 0:
            flash(f'Cannot delete category. It has {products_count} products associated with it.', 'error')
            return redirect(url_for('admin.admin_categories'))
        
        # Delete category
        result = mongo_db.db.categories.delete_one({'_id': category_object_id})
        
        if result.deleted_count > 0:
            flash('Category has been deleted successfully!', 'success')
        else:
            flash('Category not found.', 'error')
            
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_categories'))