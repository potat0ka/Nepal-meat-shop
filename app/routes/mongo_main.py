#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Main Routes
Homepage, search, and general page routes for MongoDB.
"""

from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app
import os
from app.utils.mongo_db import mongo_db

# Create main blueprint
mongo_main_bp = Blueprint('main', __name__)

@mongo_main_bp.route('/')
def index():
    """
    Homepage with featured products and categories.
    """
    # Get featured products
    featured_products = mongo_db.get_featured_products()[:6]  # Limit to 6 products
    
    # Get all categories
    categories = mongo_db.get_all_categories()
    
    # Get recent products
    recent_products = mongo_db.get_all_products()[:8]  # Limit to 8 products
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         categories=categories,
                         recent_products=recent_products)

@mongo_main_bp.route('/search')
def search():
    """
    Search products by name, category, or meat type.
    """
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    meat_type = request.args.get('meat_type', '').strip()
    
    if not query and not category and not meat_type:
        return render_template('products/list.html', 
                             products=[], 
                             search_query='',
                             message='कृपया खोज शब्द प्रविष्ट गर्नुहोस् / Please enter search terms')
    
    # Build search criteria
    search_criteria = {'is_available': True}
    
    if query:
        # Search in product name and description
        search_criteria['$or'] = [
            {'name': {'$regex': query, '$options': 'i'}},
            {'name_nepali': {'$regex': query, '$options': 'i'}},
            {'description': {'$regex': query, '$options': 'i'}}
        ]
    
    if category:
        search_criteria['category'] = category
    
    if meat_type:
        search_criteria['meat_type'] = meat_type
    
    # Perform search using MongoDB aggregation
    products_data = mongo_db.db.products.find(search_criteria).sort('name', 1)
    products = [mongo_db.MongoProduct(product_data) for product_data in products_data]
    
    return render_template('products/list.html', 
                         products=products,
                         search_query=query,
                         selected_category=category,
                         selected_meat_type=meat_type)

@mongo_main_bp.route('/api/search-suggestions')
def search_suggestions():
    """
    API endpoint for search suggestions.
    """
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    # Search for product names that match the query
    suggestions_data = mongo_db.db.products.find({
        'is_available': True,
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'name_nepali': {'$regex': query, '$options': 'i'}}
        ]
    }).limit(10)
    
    suggestions = []
    for product_data in suggestions_data:
        suggestions.append({
            'name': product_data['name'],
            'name_nepali': product_data.get('name_nepali', ''),
            'category': product_data.get('category', ''),
            'id': str(product_data['_id'])
        })
    
    return jsonify(suggestions)

@mongo_main_bp.route('/about')
def about():
    """
    About page with company information.
    """
    return render_template('about.html')

@mongo_main_bp.route('/contact')
def contact():
    """
    Contact page with contact information.
    """
    return render_template('contact.html')



@mongo_main_bp.route('/api/categories')
def api_categories():
    """
    API endpoint to get all categories.
    """
    categories = mongo_db.get_all_categories()
    categories_data = []
    
    for category in categories:
        categories_data.append({
            'id': str(category._id),
            'name': category.name,
            'name_nepali': category.name_nepali,
            'description': category.description
        })
    
    return jsonify(categories_data)

@mongo_main_bp.route('/api/meat-types')
def api_meat_types():
    """
    API endpoint to get available meat types.
    """
    # Get distinct meat types from products
    meat_types = mongo_db.db.products.distinct('meat_type', {'is_available': True})
    
    return jsonify(meat_types)

@mongo_main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Serve uploaded files (images, etc.).
    Supports subdirectories like profiles/, products/, etc.
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    response = send_from_directory(upload_folder, filename)
    
    # Set correct MIME type for SVG files
    if filename.lower().endswith('.svg'):
        response.headers['Content-Type'] = 'image/svg+xml'
    
    return response