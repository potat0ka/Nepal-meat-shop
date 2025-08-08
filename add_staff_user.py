#!/usr/bin/env python3
"""
Script to add a staff user to the MongoDB database.
"""

import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.mongo')

from app.utils.mongo_db import MongoDB
from app.config.mongo_settings import mongo_config

# Initialize MongoDB connection
mongo_db = MongoDB()

# Initialize with app context
from flask import Flask
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(mongo_config[config_name])

with app.app_context():
    mongo_db.init_app(app)

# Staff user data
staff_user = {
    'username': 'staff1',
    'email': 'staff@meatshop.com',
    'password_hash': generate_password_hash('staff123'),
    'full_name': 'Staff Member',
    'phone': '+977-9841234569',
    'address': 'Bhaktapur, Nepal',
    'is_admin': False,
    'is_sub_admin': False,
    'is_staff': True,
    'is_active': True,
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}

try:
    # Check if staff user already exists
    existing_user = mongo_db.db.users.find_one({'username': 'staff1'})
    if existing_user:
        print("Staff user already exists!")
    else:
        # Add staff user
        result = mongo_db.db.users.insert_one(staff_user)
        print(f"✅ Staff user created successfully with ID: {result.inserted_id}")
        print("Login credentials:")
        print("Username: staff1")
        print("Password: staff123")
        
except Exception as e:
    print(f"❌ Error creating staff user: {e}")