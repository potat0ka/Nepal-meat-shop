#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Products Routes
Product listing, details, and management routes for MongoDB.
"""

from flask import Blueprint, render_template, request, jsonify, abort
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoProduct
from app.forms.order import CartForm
from app.forms.product import ReviewForm
from bson.objectid import ObjectId

# Create products blueprint
mongo_products_bp = Blueprint('products', __name__, url_prefix='/products')

@mongo_products_bp.route('/')
def list():
    """
    Product listing page with filtering and pagination.
    """
    # Get filter parameters
    category = request.args.get('category', '').strip()
    meat_type = request.args.get('meat_type', '').strip()
    preparation_type = request.args.get('preparation_type', '').strip()
    price_range = request.args.get('price_range', '').strip()
    sort_by = request.args.get('sort', 'name')  # name, price_low, price_high, newest
    page = int(request.args.get('page', 1))
    per_page = 12
    
    # Build query
    query = {'is_available': True}
    
    if category:
        # Handle both category ID and category name
        if category.isdigit():
            # If it's a number, find category by ID and get its name
            category_obj = mongo_db.find_category_by_id(category)
            if category_obj:
                query['category'] = category_obj.name
        else:
            # If it's a string, use it directly as category name
            query['category'] = category
    
    if meat_type:
        query['meat_type'] = meat_type
    
    if preparation_type:
        query['preparation_type'] = preparation_type
    
    # Add price range filtering
    if price_range:
        if price_range == 'under_500':
            query['price'] = {'$lt': 500}
        elif price_range == '500_750':
            query['price'] = {'$gte': 500, '$lt': 750}
        elif price_range == '750_1000':
            query['price'] = {'$gte': 750, '$lt': 1000}
        elif price_range == 'above_1000':
            query['price'] = {'$gte': 1000}
    
    # Build sort criteria
    sort_criteria = []
    if sort_by == 'price_low':
        sort_criteria = [('price', 1)]
    elif sort_by == 'price_high':
        sort_criteria = [('price', -1)]
    elif sort_by == 'newest':
        sort_criteria = [('date_added', -1)]
    else:  # default to name
        sort_criteria = [('name', 1)]
    
    # Get total count for pagination
    total_products = mongo_db.db.products.count_documents(query)
    
    # Calculate pagination
    total_pages = (total_products + per_page - 1) // per_page
    skip = (page - 1) * per_page
    
    # Get products for current page
    products_data = mongo_db.db.products.find(query).sort(sort_criteria).skip(skip).limit(per_page)
    products = [MongoProduct(product_data) for product_data in products_data]
    
    # Get categories for filter
    categories = mongo_db.get_all_categories()
    
    # Get available meat types and preparation types
    meat_types = mongo_db.db.products.distinct('meat_type', {'is_available': True})
    preparation_types = mongo_db.db.products.distinct('preparation_type', {'is_available': True})
    
    # Create pagination object (similar to SQLAlchemy pagination)
    class Pagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    pagination = Pagination(page, per_page, total_products, products)
    
    return render_template('products/list.html',
                         products=pagination,
                         categories=categories,
                         meat_types=meat_types,
                         preparation_types=preparation_types,
                         current_category=category,
                         current_meat_type=meat_type,
                         current_preparation_type=preparation_type,
                         current_price_range=price_range,
                         current_sort=sort_by)

@mongo_products_bp.route('/<product_id>')
def detail(product_id):
    """
    Product detail page with full information.
    """
    try:
        # Find product by ID
        product = mongo_db.find_product_by_id(product_id)
        
        if not product:
            abort(404)
        
        if not product.is_available:
            abort(404)
        
        # Create forms for the template
        form = CartForm()
        review_form = ReviewForm()
        
        # Get related products (same category, different product)
        related_products_data = mongo_db.db.products.find({
            'category': product.category,
            'is_available': True,
            '_id': {'$ne': ObjectId(product_id)}
        }).limit(4)
        
        related_products = [MongoProduct(product_data) for product_data in related_products_data]
        
        # Get product reviews (if implemented)
        # reviews = mongo_db.get_product_reviews(product_id)
        reviews = []  # Placeholder for now
        
        return render_template('products/detail.html',
                             product=product,
                             related_products=related_products,
                             reviews=reviews,
                             form=form,
                             review_form=review_form)
    
    except Exception as e:
        abort(404)

@mongo_products_bp.route('/category/<category_name>')
def by_category(category_name):
    """
    Products filtered by category.
    """
    # Get products in this category
    products = mongo_db.get_all_products(category=category_name)
    
    # Get category info
    category = mongo_db.find_category_by_name(category_name)
    
    if not category:
        abort(404)
    
    return render_template('products/category.html',
                         products=products,
                         category=category)

@mongo_products_bp.route('/meat-type/<meat_type>')
def by_meat_type(meat_type):
    """
    Products filtered by meat type.
    """
    # Get products of this meat type
    products = mongo_db.get_all_products(meat_type=meat_type)
    
    if not products:
        abort(404)
    
    return render_template('products/meat_type.html',
                         products=products,
                         meat_type=meat_type)

@mongo_products_bp.route('/api/<product_id>')
def api_product_detail(product_id):
    """
    API endpoint for product details.
    """
    try:
        product = mongo_db.find_product_by_id(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        product_data = {
            'id': str(product._id),
            'name': product.name,
            'name_nepali': product.name_nepali,
            'description': product.description,
            'price': product.price,
            'image_url': product.image_url,
            'category': product.category,
            'meat_type': product.meat_type,
            'preparation_type': product.preparation_type,
            'stock_quantity': product.stock_quantity,
            'unit': product.unit,
            'is_featured': product.is_featured,
            'is_available': product.is_available
        }
        
        return jsonify(product_data)
    
    except Exception as e:
        return jsonify({'error': 'Invalid product ID'}), 400

@mongo_products_bp.route('/api/check-stock/<product_id>')
def api_check_stock(product_id):
    """
    API endpoint to check product stock.
    """
    try:
        product = mongo_db.find_product_by_id(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'product_id': str(product._id),
            'stock_quantity': product.stock_quantity,
            'is_available': product.is_available,
            'unit': product.unit
        })
    
    except Exception as e:
        return jsonify({'error': 'Invalid product ID'}), 400