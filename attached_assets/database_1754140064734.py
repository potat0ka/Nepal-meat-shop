
"""
Database Management Utility for Nepal Meat Shop
This file handles database initialization, admin user creation, and sample data setup
"""

from app import app, db
from models import (User, Category, Product, DeliveryArea, NotificationTemplate, 
                   StockAlert, SalesReport)
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def init_database():
    """Initialize database and create all tables."""
    print("🔄 Initializing database...")
    
    with app.app_context():
        try:
            # Drop all tables (use with caution in production)
            db.drop_all()
            print("✅ Dropped all existing tables")
            
            # Create all tables
            db.create_all()
            print("✅ Created all database tables")
            
            # Create admin user
            create_admin_users()
            
            # Create sample categories
            create_sample_categories()
            
            # Create delivery areas
            create_delivery_areas()
            
            # Create notification templates
            create_notification_templates()
            
            print("🎉 Database initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()

def create_admin_users():
    """Create default admin users with different access levels."""
    print("👤 Creating admin users...")
    
    # Super Admin
    super_admin = User(
        username='superadmin',
        email='admin@meatshop.np',
        full_name='Super Administrator',
        phone='9800000001',
        address='Kathmandu, Nepal',
        is_admin=True,
        is_active=True,
        password_hash=generate_password_hash('admin123')
    )
    
    # Store Manager
    store_manager = User(
        username='storemanager',
        email='manager@meatshop.np',
        full_name='Store Manager',
        phone='9800000002',
        address='Lalitpur, Nepal',
        is_admin=True,
        is_active=True,
        password_hash=generate_password_hash('manager123')
    )
    
    # Demo Customer
    demo_customer = User(
        username='democustomer',
        email='customer@example.com',
        full_name='Demo Customer',
        phone='9800000003',
        address='Bhaktapur, Nepal',
        is_admin=False,
        is_active=True,
        password_hash=generate_password_hash('customer123')
    )
    
    db.session.add_all([super_admin, store_manager, demo_customer])
    db.session.commit()
    
    print("✅ Admin users created:")
    print("   📧 admin@meatshop.np | 🔑 admin123 (Super Admin)")
    print("   📧 manager@meatshop.np | 🔑 manager123 (Store Manager)")
    print("   📧 customer@example.com | 🔑 customer123 (Demo Customer)")

def create_sample_categories():
    """Create sample product categories."""
    print("📂 Creating product categories...")
    
    categories = [
        {
            'name': 'Pork Cuts',
            'name_nepali': 'सुंगुरको मासु',
            'description': 'Fresh pork cuts including leg, shoulder, ribs, and belly'
        },
        {
            'name': 'Buffalo Cuts',
            'name_nepali': 'भैंसीको मासु',
            'description': 'Premium buffalo meat cuts for traditional Nepali cooking'
        },
        {
            'name': 'Processed Meat',
            'name_nepali': 'प्रशोधित मासु',
            'description': 'Sausages, bacon, and other processed meat products'
        },
        {
            'name': 'Organs',
            'name_nepali': 'अंगहरू',
            'description': 'Fresh organs including liver, kidney, heart, and tongue'
        },
        {
            'name': 'Bones',
            'name_nepali': 'हड्डी',
            'description': 'Bones for soup and broth making'
        }
    ]
    
    for cat_data in categories:
        category = Category(
            name=cat_data['name'],
            name_nepali=cat_data['name_nepali'],
            description=cat_data['description'],
            is_active=True
        )
        db.session.add(category)
    
    db.session.commit()
    print("✅ Sample categories created")

def create_delivery_areas():
    """Create delivery areas for Kathmandu Valley."""
    print("🚚 Creating delivery areas...")
    
    areas = [
        {
            'area_name': 'Kathmandu Core',
            'area_name_nepali': 'काठमाडौं मुख्य',
            'delivery_charge': 50.0,
            'min_order_amount': 500.0,
            'delivery_time_hours': 2
        },
        {
            'area_name': 'Lalitpur',
            'area_name_nepali': 'ललितपुर',
            'delivery_charge': 60.0,
            'min_order_amount': 600.0,
            'delivery_time_hours': 3
        },
        {
            'area_name': 'Bhaktapur',
            'area_name_nepali': 'भक्तपुर',
            'delivery_charge': 75.0,
            'min_order_amount': 800.0,
            'delivery_time_hours': 4
        },
        {
            'area_name': 'Kirtipur',
            'area_name_nepali': 'कीर्तिपुर',
            'delivery_charge': 80.0,
            'min_order_amount': 700.0,
            'delivery_time_hours': 3
        }
    ]
    
    for area_data in areas:
        area = DeliveryArea(
            area_name=area_data['area_name'],
            area_name_nepali=area_data['area_name_nepali'],
            delivery_charge=area_data['delivery_charge'],
            min_order_amount=area_data['min_order_amount'],
            delivery_time_hours=area_data['delivery_time_hours'],
            is_active=True
        )
        db.session.add(area)
    
    db.session.commit()
    print("✅ Delivery areas created")

def create_notification_templates():
    """Create email and SMS notification templates."""
    print("📧 Creating notification templates...")
    
    templates = [
        {
            'name': 'Order Confirmation Email',
            'type': 'email',
            'event': 'order_placed',
            'subject': 'Order Confirmation - Nepal Meat Shop',
            'body_template': '''
            Dear {customer_name},
            
            Thank you for your order! Your order #{order_number} has been received.
            
            Order Details:
            - Total Amount: NPR {total_amount}
            - Delivery Address: {delivery_address}
            - Expected Delivery: {delivery_date}
            
            We will notify you once your order is confirmed and prepared.
            
            Best regards,
            Nepal Meat Shop Team
            '''
        },
        {
            'name': 'Order Status Update Email',
            'type': 'email',
            'event': 'order_status_change',
            'subject': 'Order Status Update - Nepal Meat Shop',
            'body_template': '''
            Dear {customer_name},
            
            Your order #{order_number} status has been updated to: {status}
            
            {status_message}
            
            Track your order or contact us for any queries.
            
            Best regards,
            Nepal Meat Shop Team
            '''
        },
        {
            'name': 'Low Stock Alert Email',
            'type': 'email',
            'event': 'low_stock',
            'subject': 'Low Stock Alert - {product_name}',
            'body_template': '''
            Alert: Product "{product_name}" is running low on stock.
            
            Current Stock: {current_stock} kg
            Threshold: {threshold} kg
            
            Please restock immediately to avoid out-of-stock situations.
            '''
        }
    ]
    
    for template_data in templates:
        template = NotificationTemplate(
            name=template_data['name'],
            type=template_data['type'],
            event=template_data['event'],
            subject=template_data.get('subject'),
            body_template=template_data['body_template'],
            is_active=True
        )
        db.session.add(template)
    
    db.session.commit()
    print("✅ Notification templates created")

def reset_database():
    """Reset database completely (CAUTION: This will delete all data)."""
    print("⚠️  WARNING: This will delete ALL data!")
    confirmation = input("Type 'RESET' to confirm: ")
    
    if confirmation == 'RESET':
        init_database()
    else:
        print("❌ Database reset cancelled")

def show_admin_credentials():
    """Display admin login credentials."""
    print("\n" + "="*50)
    print("🔐 ADMIN LOGIN CREDENTIALS")
    print("="*50)
    print("Super Admin:")
    print("  📧 Email: admin@meatshop.np")
    print("  🔑 Password: admin123")
    print("")
    print("Store Manager:")
    print("  📧 Email: manager@meatshop.np") 
    print("  🔑 Password: manager123")
    print("")
    print("Demo Customer:")
    print("  📧 Email: customer@example.com")
    print("  🔑 Password: customer123")
    print("="*50)

def check_database_status():
    """Check database connection and table status."""
    print("🔍 Checking database status...")
    
    with app.app_context():
        try:
            # Test database connection
            db.engine.execute("SELECT 1")
            print("✅ Database connection: OK")
            
            # Check tables
            tables = db.engine.table_names()
            print(f"✅ Tables found: {len(tables)}")
            for table in tables:
                print(f"   - {table}")
            
            # Check admin users
            admin_count = User.query.filter_by(is_admin=True).count()
            print(f"✅ Admin users: {admin_count}")
            
            # Check categories
            category_count = Category.query.count()
            print(f"✅ Categories: {category_count}")
            
            # Check products
            product_count = Product.query.count()
            print(f"✅ Products: {product_count}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")

if __name__ == '__main__':
    print("🍖 Nepal Meat Shop - Database Management")
    print("="*40)
    print("1. Initialize Database")
    print("2. Reset Database (Delete All)")
    print("3. Show Admin Credentials")
    print("4. Check Database Status")
    print("5. Exit")
    print("="*40)
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            init_database()
            show_admin_credentials()
        elif choice == '2':
            reset_database()
        elif choice == '3':
            show_admin_credentials()
        elif choice == '4':
            check_database_status()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
