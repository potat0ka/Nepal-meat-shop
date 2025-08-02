"""
Database initialization and management utilities.
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with sample data."""
    try:
        from app import app, db
        from models import User, Category, Product, DeliveryArea
        
        with app.app_context():
            print("🔧 Initializing database...")
            
            # Create all tables
            db.create_all()
            
            # Create admin user if not exists
            admin = User.query.filter_by(email='admin@meatshop.np').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@meatshop.np',
                    full_name='Admin User',
                    phone='9841234567',
                    address='Kathmandu, Nepal',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin user created")
            
            # Create categories if not exist
            categories_data = [
                {'name': 'Pork Cuts', 'name_nepali': 'सुंगुरको मासु', 'description': 'Fresh pork cuts'},
                {'name': 'Buffalo Cuts', 'name_nepali': 'भैंसीको मासु', 'description': 'Fresh buffalo meat cuts'},
                {'name': 'Processed Meat', 'name_nepali': 'प्रशोधित मासु', 'description': 'Sausages, bacon, etc.'},
                {'name': 'Ground Meat', 'name_nepali': 'पिसेको मासु', 'description': 'Ground/minced meat'}
            ]
            
            for cat_data in categories_data:
                if not Category.query.filter_by(name=cat_data['name']).first():
                    category = Category(**cat_data)
                    db.session.add(category)
            
            # Create delivery areas
            delivery_areas_data = [
                {'area_name': 'Kathmandu Central', 'area_name_nepali': 'काठमाडौं केन्द्र', 'delivery_charge': 50.0},
                {'area_name': 'Lalitpur', 'area_name_nepali': 'ललितपुर', 'delivery_charge': 75.0},
                {'area_name': 'Bhaktapur', 'area_name_nepali': 'भक्तपुर', 'delivery_charge': 100.0},
                {'area_name': 'Kirtipur', 'area_name_nepali': 'कीर्तिपुर', 'delivery_charge': 80.0}
            ]
            
            for area_data in delivery_areas_data:
                if not DeliveryArea.query.filter_by(area_name=area_data['area_name']).first():
                    area = DeliveryArea(**area_data)
                    db.session.add(area)
            
            # Create sample products
            if Category.query.count() > 0:
                pork_category = Category.query.filter_by(name='Pork Cuts').first()
                buffalo_category = Category.query.filter_by(name='Buffalo Cuts').first()
                
                sample_products = [
                    {
                        'name': 'Pork Shoulder',
                        'name_nepali': 'सुंगुरको काँध',
                        'description': 'Fresh pork shoulder, perfect for roasting and slow cooking',
                        'price': 800.0,
                        'category_id': pork_category.id if pork_category else 1,
                        'meat_type': 'pork',
                        'stock_kg': 25.0,
                        'is_featured': True,
                        'cooking_tips': 'Best when slow-cooked or roasted'
                    },
                    {
                        'name': 'Buffalo Steak',
                        'name_nepali': 'भैंसीको स्टेक',
                        'description': 'Premium buffalo steak cuts, tender and flavorful',
                        'price': 1200.0,
                        'category_id': buffalo_category.id if buffalo_category else 2,
                        'meat_type': 'buffalo',
                        'stock_kg': 15.0,
                        'is_featured': True,
                        'cooking_tips': 'Grill or pan-fry for best results'
                    }
                ]
                
                for prod_data in sample_products:
                    if not Product.query.filter_by(name=prod_data['name']).first():
                        product = Product(**prod_data)
                        db.session.add(product)
            
            # Commit all changes
            db.session.commit()
            print("✅ Database initialized successfully!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

def show_admin_credentials():
    """Display admin login credentials."""
    print("\n🔑 Admin Login Credentials:")
    print("Email: admin@meatshop.np")
    print("Password: admin123")
    print("")

def check_database_status():
    """Check database status and show statistics."""
    try:
        from app import app, db
        from models import User, Category, Product, Order
        
        with app.app_context():
            users_count = User.query.count()
            categories_count = Category.query.count()
            products_count = Product.query.count()
            orders_count = Order.query.count()
            
            print(f"👥 Users: {users_count}")
            print(f"📂 Categories: {categories_count}")
            print(f"🥩 Products: {products_count}")
            print(f"📦 Orders: {orders_count}")
            
            admin_count = User.query.filter_by(is_admin=True).count()
            print(f"🔑 Admin users: {admin_count}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == '__main__':
    init_database()
    show_admin_credentials()
    check_database_status()
