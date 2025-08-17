#!/usr/bin/env python3
"""
Check Session Script
This script checks the current user session and login status.
"""

import os
import sys
from flask import Flask
from flask_login import current_user
from dotenv import load_dotenv

# Add backend directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
backend_dir = os.path.join(parent_dir, 'backend')
sys.path.insert(0, backend_dir)

# Change to backend directory and load environment variables
os.chdir(backend_dir)
load_dotenv('.env.mongo')

from app.utils.mongo_db import MongoDB
from app.models.mongo_models import MongoUser
from app import create_app

def check_session():
    """Check current session status."""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Session Check Results:")
        print("=" * 40)
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            print(f"✅ User is logged in")
            print(f"👤 Username: {current_user.username}")
            print(f"📧 Email: {current_user.email}")
            print(f"📛 Full Name: {current_user.full_name}")
            print(f"🔰 Is Admin: {current_user.is_admin}")
            print(f"🔰 Is Sub Admin: {current_user.is_sub_admin}")
            print(f"🔰 Is Staff: {current_user.is_staff}")
            print(f"🔰 Has Admin Access: {current_user.has_admin_access()}")
            print(f"📊 Is Active: {current_user.is_active}")
        else:
            print("❌ No user is currently logged in")
            print("💡 You need to log in through the web interface first")

if __name__ == '__main__':
    print("🍖 Nepal Meat Shop - Session Check")
    print("=" * 40)
    check_session()