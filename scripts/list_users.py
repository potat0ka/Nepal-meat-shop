#!/usr/bin/env python3
"""
List Users Script
This script lists all users in the Nepal Meat Shop database.
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Add backend directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
backend_dir = os.path.join(parent_dir, 'backend')
sys.path.insert(0, backend_dir)

# Change to backend directory and load environment variables
os.chdir(backend_dir)
load_dotenv('.env.mongo')

def list_users():
    """List all users in the database."""
    
    # MongoDB connection
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    db_name = os.environ.get('MONGO_DBNAME', 'nepal_meat_shop_dev')
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    try:
        # Get all users
        users = db.users.find()
        
        print("📋 Users in Database:")
        print("=" * 60)
        
        for user in users:
            role = "Admin" if user.get('is_admin') else ("Sub-Admin" if user.get('is_sub_admin') else ("Staff" if user.get('is_staff') else "Customer"))
            status = "Active" if user.get('is_active', True) else "Inactive"
            
            print(f"🆔 ID: {user['_id']}")
            print(f"👤 Username: {user.get('username', 'N/A')}")
            print(f"📧 Email: {user.get('email', 'N/A')}")
            print(f"📛 Full Name: {user.get('full_name', 'N/A')}")
            print(f"🔰 Role: {role}")
            print(f"📊 Status: {status}")
            print(f"📅 Joined: {user.get('date_joined', 'N/A')}")
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
    
    finally:
        client.close()

if __name__ == '__main__':
    print("🍖 Nepal Meat Shop - User List")
    print("=" * 40)
    list_users()