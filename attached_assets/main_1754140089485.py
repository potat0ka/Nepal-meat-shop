
#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Main Entry Point
Pork and Buffalo meat shop platform for Nepal
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main application entry point."""
    try:
        from app import app
        
        # Run the application
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"🍖 Starting Nepal Meat Shop on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Try running 'python install_dependencies.py' first")
        sys.exit(1)

if __name__ == '__main__':
    main()
