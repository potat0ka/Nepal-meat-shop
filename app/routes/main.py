#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Main Routes
Home page, general pages, and core application routes.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoProduct, MongoCategory
from app.utils import get_stock_status, format_currency

# Create main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Homepage with featured products, recent products, and categories.
    Displays the main landing page for the meat shop.
    """
    try:
        # Get featured products (marked as featured and active)
        featured_products_data = mongo_db.db.products.find({
            'is_featured': True, 
            'is_available': True
        }).limit(6)
        featured_products = [MongoProduct(product_data) for product_data in featured_products_data]

        # Get recent products (newest first)
        recent_products_data = mongo_db.db.products.find({
            'is_available': True
        }).sort('created_at', -1).limit(8)
        recent_products = [MongoProduct(product_data) for product_data in recent_products_data]

        # Get active categories
        categories = mongo_db.get_all_categories()

        return render_template('index.html', 
                             featured_products=featured_products,
                             recent_products=recent_products,
                             categories=categories)
    
    except Exception as e:
        current_app.logger.error(f"Error loading homepage: {e}")
        # Return basic homepage even if there's an error
        return render_template('index.html', 
                             featured_products=[],
                             recent_products=[],
                             categories=[])

@main_bp.route('/about')
def about():
    """
    About us page with shop information.
    """
    return render_template('pages/about.html')

@main_bp.route('/contact')
def contact():
    """
    Contact us page with shop details and contact form.
    """
    return render_template('pages/contact.html')

@main_bp.route('/delivery-info')
def delivery_info():
    """
    Delivery information and areas covered.
    """
    return render_template('pages/delivery_info.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    """
    Privacy policy page.
    """
    return render_template('pages/privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    """
    Terms of service page.
    """
    return render_template('pages/terms_of_service.html')

@main_bp.route('/search')
def search():
    """
    Search products by name or description.
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('products/search_results.html', 
                             products=[], 
                             query='',
                             total_results=0)
    
    # Search in product name, name_nepali, and description
    search_filter = {
        'is_available': True,
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'name_nepali': {'$regex': query, '$options': 'i'}},
            {'description': {'$regex': query, '$options': 'i'}}
        ]
    }
    products_data = mongo_db.db.products.find(search_filter).sort('name', 1)
    products = [MongoProduct(product_data) for product_data in products_data]
    
    return render_template('products/search_results.html', 
                         products=products, 
                         query=query,
                         total_results=len(products))

@main_bp.route('/api/product-stock/<int:product_id>')
def api_product_stock(product_id):
    """
    API endpoint to get current stock status for a product.
    Returns JSON with stock information.
    """
    try:
        product = mongo_db.find_product_by_id(product_id)
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
            
        stock_status = get_stock_status(product)
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'stock_kg': product.stock_quantity,
            'status': stock_status,
            'price': product.price,
            'formatted_price': format_currency(product.price)
        })
    
    except Exception as e:
        current_app.logger.error(f"Error getting stock for product {product_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404

@main_bp.route('/api/categories')
def api_categories():
    """
    API endpoint to get all active categories.
    Returns JSON list of categories.
    """
    try:
        categories = mongo_db.get_all_categories()
        
        category_list = []
        for category in categories:
            # Count products in this category
            product_count = mongo_db.db.products.count_documents({
                'category_id': str(category._id),
                'is_available': True
            })
            
            category_list.append({
                'id': str(category._id),
                'name': category.name,
                'name_nepali': category.name_nepali,
                'description': category.description,
                'product_count': product_count
            })
        
        return jsonify({
            'success': True,
            'categories': category_list
        })
    
    except Exception as e:
        current_app.logger.error(f"Error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load categories'
        }), 500

@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        # Simple database connectivity check
        category_count = mongo_db.db.categories.count_documents({})
        product_count = mongo_db.db.products.count_documents({})
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'categories': category_count,
            'products': product_count
        })
    
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Template context processors
@main_bp.app_context_processor
def inject_template_globals():
    """
    Inject global variables into all templates.
    """
    return {
        'format_currency': format_currency,
        'get_stock_status': get_stock_status
    }