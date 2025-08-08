#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Product Routes
Product listing, details, reviews, and product-related functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Category, Review
from app.forms import ReviewForm, ProductFilterForm
from app.utils import get_stock_status, format_currency, truncate_text

# Create products blueprint
products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
def list():
    """
    Product listing page with filtering and sorting options.
    """
    # Get filter parameters from URL
    category_id = request.args.get('category', type=int)
    meat_type = request.args.get('meat_type')
    preparation_type = request.args.get('preparation_type')
    sort_by = request.args.get('sort', 'name')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Products per page

    # Build base query for active products
    query = Product.query.filter_by(is_active=True)

    # Apply filters
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
    elif sort_by == 'popular':
        # Sort by number of orders (if we have that relationship)
        query = query.order_by(Product.name.asc())  # Fallback to name
    else:
        query = query.order_by(Product.name.asc())

    # Paginate results
    products = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

    # Get categories for filter dropdown
    categories = Category.query.filter_by(is_active=True).all()

    # Get unique meat types and preparation types for filters
    meat_types = db.session.query(Product.meat_type).filter(
        Product.is_active == True,
        Product.meat_type.isnot(None)
    ).distinct().all()
    meat_types = [mt[0] for mt in meat_types if mt[0]]

    preparation_types = db.session.query(Product.preparation_type).filter(
        Product.is_active == True,
        Product.preparation_type.isnot(None)
    ).distinct().all()
    preparation_types = [pt[0] for pt in preparation_types if pt[0]]

    return render_template('products/list.html', 
                         products=products,
                         categories=categories,
                         meat_types=meat_types,
                         preparation_types=preparation_types,
                         current_category=category_id,
                         current_meat_type=meat_type,
                         current_preparation_type=preparation_type,
                         current_sort=sort_by)

@products_bp.route('/<int:product_id>')
def detail(product_id):
    """
    Product detail page with reviews and related products.
    """
    product = Product.query.get_or_404(product_id)
    
    # Check if product is active
    if not product.is_active:
        flash('यो उत्पादन उपलब्ध छैन / Product not available', 'error')
        return redirect(url_for('products.list'))

    # Get approved reviews for this product
    reviews = Review.query.filter_by(
        product_id=product_id, 
        is_approved=True
    ).order_by(Review.created_at.desc()).all()

    # Get related products from same category
    related_products = Product.query.filter_by(
        category_id=product.category_id, 
        is_active=True
    ).filter(Product.id != product_id).limit(4).all()

    # Create review form for logged-in users
    review_form = ReviewForm() if current_user.is_authenticated else None

    # Check if current user has already reviewed this product
    user_has_reviewed = False
    if current_user.is_authenticated:
        user_has_reviewed = Review.query.filter_by(
            product_id=product_id,
            user_id=current_user.id
        ).first() is not None

    return render_template('products/detail.html', 
                         product=product,
                         reviews=reviews,
                         related_products=related_products,
                         review_form=review_form,
                         user_has_reviewed=user_has_reviewed)

@products_bp.route('/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """
    Add a review for a product.
    """
    product = Product.query.get_or_404(product_id)
    
    # Check if user has already reviewed this product
    existing_review = Review.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('तपाईंले यो उत्पादनको समीक्षा पहिले नै गर्नुभएको छ / You have already reviewed this product', 'warning')
        return redirect(url_for('products.detail', product_id=product_id))

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            product_id=product_id,
            user_id=current_user.id,
            rating=form.rating.data,
            comment=form.comment.data,
            is_approved=False  # Reviews need approval
        )

        try:
            db.session.add(review)
            db.session.commit()
            flash('समीक्षा पेश गरियो! अनुमोदन पछि देखाइनेछ / Review submitted! It will appear after approval.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('समीक्षा पेश गर्दा समस्या भयो / Error submitting review', 'error')
    else:
        flash('समीक्षा फारममा त्रुटि छ / Review form has errors', 'error')

    return redirect(url_for('products.detail', product_id=product_id))

@products_bp.route('/category/<int:category_id>')
def by_category(category_id):
    """
    Products filtered by category.
    """
    category = Category.query.get_or_404(category_id)
    
    if not category.is_active:
        flash('यो श्रेणी उपलब्ध छैन / Category not available', 'error')
        return redirect(url_for('products.list'))

    # Redirect to main product list with category filter
    return redirect(url_for('products.list', category=category_id))

@products_bp.route('/search')
def search():
    """
    Search products by name, description, or other criteria.
    """
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12

    if not query:
        flash('खोज शब्द आवश्यक छ / Search term required', 'warning')
        return redirect(url_for('products.list'))

    # Build search query
    search_query = Product.query.filter(
        Product.is_active == True,
        (Product.name.ilike(f'%{query}%') | 
         Product.name_nepali.ilike(f'%{query}%') |
         Product.description.ilike(f'%{query}%'))
    )

    # Apply category filter if specified
    if category_id:
        search_query = search_query.filter_by(category_id=category_id)

    # Paginate results
    products = search_query.order_by(Product.name.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    categories = Category.query.filter_by(is_active=True).all()

    return render_template('products/search_results.html',
                         products=products,
                         categories=categories,
                         query=query,
                         current_category=category_id)

@products_bp.route('/api/<int:product_id>/stock')
def api_stock_check(product_id):
    """
    API endpoint to check product stock status.
    """
    try:
        product = Product.query.get_or_404(product_id)
        stock_status = get_stock_status(product)
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'stock_kg': product.stock_kg,
            'status': stock_status,
            'price': product.price,
            'formatted_price': format_currency(product.price),
            'is_available': product.stock_kg > 0
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404

# Template filters for products
@products_bp.app_template_filter('stock_status')
def stock_status_filter(product):
    """Template filter to get stock status."""
    return get_stock_status(product)

@products_bp.app_template_filter('truncate_description')
def truncate_description_filter(text, length=150):
    """Template filter to truncate product descriptions."""
    return truncate_text(text, length)