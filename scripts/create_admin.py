#!/usr/bin/env python3
"""
Create Admin User Script
This script creates an initial admin user for the Nepal Meat Shop application.
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from pymongo import MongoClient

# Add parent directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Change to parent directory and load environment variables
os.chdir(parent_dir)
load_dotenv('.env.mongo')

def create_admin_user():
    """Create an admin user in the database."""
    
    # MongoDB connection
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    db_name = os.environ.get('MONGO_DBNAME', 'nepal_meat_shop_dev')
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # Check if admin user already exists
    existing_admin = db.users.find_one({'is_admin': True})
    if existing_admin:
        print(f"Admin user already exists: {existing_admin['email']}")
        return
    
    # Admin user data
    admin_data = {
        'username': 'admin',
        'email': 'admin@nepalmeatshop.com',
        'password_hash': generate_password_hash('admin123'),
        'full_name': 'System Administrator',
        'phone': '+977-9800000000',
        'address': 'Kathmandu, Nepal',
        'is_admin': True,
        'is_sub_admin': False,
        'is_staff': False,
        'is_active': True,
        'profile_image': None,
        'date_joined': datetime.utcnow(),
        'last_login': None,
        'reset_token': None,
        'reset_token_expiry': None
    }
    
    try:
        # Insert admin user
        result = db.users.insert_one(admin_data)
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: {admin_data['email']}")
        print(f"🔑 Password: admin123")
        print(f"🆔 User ID: {result.inserted_id}")
        print("\n⚠️  Please change the default password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
    
    finally:
        client.close()

if __name__ == '__main__':
    print("🍖 Nepal Meat Shop - Admin User Creation")
    print("=" * 40)
    create_admin_user()