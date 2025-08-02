#!/usr/bin/env python3
"""
🚀 Nepal Meat Shop - Local Development Server
Simple script to run the application locally with proper configuration.
"""

import os
import sys

def main():
    """Run the Flask application in development mode."""
    print("🍖 Starting Nepal Meat Shop...")
    print("=" * 40)
    
    # Set environment variables for development
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', 'True')
    
    try:
        # Import and run the app
        from app import app
        
        print("✅ Application loaded successfully!")
        print("🌐 Server starting on http://localhost:5000")
        print("🔑 Admin login: admin@meatshop.np / admin123")
        print("⏹️ Press Ctrl+C to stop the server")
        print("-" * 40)
        
        # Run the Flask development server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run 'python fix_database.py' first to initialize the database")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
