#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Application Runner
Run the Flask application with MongoDB backend.
"""

import os
import sys
from mongo_app import create_mongo_app
from app.utils.mongo_db import mongo_db

def main():
    """
    Main function to run the MongoDB application.
    """
    # Create the Flask app
    app = create_mongo_app()
    
    # Test MongoDB connection
    try:
        with app.app_context():
            # Test connection
            mongo_db.db.command('ping')
            print("✅ MongoDB connection successful!")
            print("✅ Database initialized!")
            
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Please make sure MongoDB is running and accessible.")
        sys.exit(1)
    
    # Run the application
    print("🍖 Starting Nepal Meat Shop with MongoDB...")
    print("🌐 Application will be available at: http://127.0.0.1:5000")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=True
    )

if __name__ == '__main__':
    main()