#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Application Runner for macOS
Run the Flask application with MongoDB backend on macOS systems.
"""

import os
import sys
import subprocess
import time
import signal
from mongo_app import create_mongo_app
from app.utils.mongo_db import mongo_db

def check_homebrew():
    """Check if Homebrew is installed."""
    try:
        subprocess.run(['brew', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_mongodb_installed():
    """Check if MongoDB is installed on macOS."""
    try:
        # Check if mongod is available
        result = subprocess.run(['which', 'mongod'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, None
    except Exception:
        return False, None

def check_mongodb_running():
    """Check if MongoDB service is running on macOS."""
    try:
        # Check if MongoDB process is running
        result = subprocess.run(['pgrep', '-f', 'mongod'], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def start_mongodb_service():
    """Start MongoDB service on macOS."""
    print("🔄 Attempting to start MongoDB service...")
    
    try:
        # Try to start with brew services
        result = subprocess.run(['brew', 'services', 'start', 'mongodb-community'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB service started with Homebrew")
            time.sleep(3)  # Wait for service to start
            return True
    except Exception as e:
        print(f"⚠️  Could not start with brew services: {e}")
    
    try:
        # Try to start manually
        print("🔄 Trying to start MongoDB manually...")
        # Create data directory if it doesn't exist
        data_dir = os.path.expanduser("~/data/db")
        os.makedirs(data_dir, exist_ok=True)
        
        # Start mongod in background
        subprocess.Popen(['mongod', '--dbpath', data_dir], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(5)  # Wait for MongoDB to start
        
        if check_mongodb_running():
            print("✅ MongoDB started manually")
            return True
    except Exception as e:
        print(f"❌ Could not start MongoDB manually: {e}")
    
    return False

def install_mongodb_mac():
    """Guide user to install MongoDB on macOS."""
    print("\n📦 MongoDB is not installed on your system.")
    print("To install MongoDB on macOS, run the following commands:")
    print("\n1. Install Homebrew (if not already installed):")
    print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    print("\n2. Install MongoDB:")
    print("   brew tap mongodb/brew")
    print("   brew install mongodb-community")
    print("\n3. Start MongoDB:")
    print("   brew services start mongodb-community")
    print("\nAlternatively, you can use MongoDB Atlas (cloud database):")
    print("   Set MONGO_URI environment variable to your Atlas connection string")
    
def setup_environment():
    """Setup macOS-specific environment variables."""
    # Set default MongoDB URI for macOS
    if not os.environ.get('MONGO_URI'):
        os.environ['MONGO_URI'] = 'mongodb://localhost:27017/nepal_meat_shop_dev'
    
    # Set Flask environment
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    # Load .env.mongo file if it exists
    env_file = '.env.mongo'
    if os.path.exists(env_file):
        print(f"📄 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def test_mongodb_connection(app):
    """Test MongoDB connection with detailed error reporting."""
    try:
        with app.app_context():
            # Test connection with timeout
            mongo_db.db.command('ping')
            print("✅ MongoDB connection successful!")
            
            # Test database operations
            collections = mongo_db.db.list_collection_names()
            print(f"📊 Database '{mongo_db.db.name}' is accessible")
            print(f"📁 Found {len(collections)} collections")
            
            return True
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ MongoDB connection failed: {e}")
        
        if 'connection refused' in error_msg:
            print("💡 MongoDB server is not running. Trying to start it...")
            return False
        elif 'authentication failed' in error_msg:
            print("💡 Authentication failed. Check your MongoDB credentials.")
            print("   Set MONGO_URI with proper username/password")
            return False
        elif 'network timeout' in error_msg:
            print("💡 Network timeout. Check your internet connection for Atlas.")
            return False
        elif 'name resolution' in error_msg:
            print("💡 DNS resolution failed. Check your MongoDB Atlas URL.")
            return False
        else:
            print("💡 Check your MongoDB configuration and try again.")
            return False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Shutting down Nepal Meat Shop...")
    sys.exit(0)

def main():
    """
    Main function to run the MongoDB application on macOS.
    """
    print("🍖 Nepal Meat Shop - macOS MongoDB Runner")
    print("=" * 50)
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup environment
    setup_environment()
    
    # Check if using cloud MongoDB (Atlas)
    mongo_uri = os.environ.get('MONGO_URI', '')
    using_atlas = 'mongodb+srv://' in mongo_uri or 'mongodb.net' in mongo_uri
    
    if not using_atlas:
        print("🔍 Checking local MongoDB setup...")
        
        # Check if MongoDB is installed
        is_installed, mongo_path = check_mongodb_installed()
        if not is_installed:
            install_mongodb_mac()
            sys.exit(1)
        
        print(f"✅ MongoDB found at: {mongo_path}")
        
        # Check if MongoDB is running
        if not check_mongodb_running():
            print("⚠️  MongoDB is not running")
            if not start_mongodb_service():
                print("❌ Could not start MongoDB service")
                print("💡 Try starting MongoDB manually:")
                print("   brew services start mongodb-community")
                print("   or")
                print("   mongod --dbpath ~/data/db")
                sys.exit(1)
    else:
        print("☁️  Using MongoDB Atlas (cloud database)")
    
    # Create the Flask app
    print("🔧 Creating Flask application...")
    app = create_mongo_app()
    
    # Test MongoDB connection
    print("🔗 Testing MongoDB connection...")
    if not test_mongodb_connection(app):
        if not using_atlas:
            # Try to start MongoDB one more time
            if start_mongodb_service():
                time.sleep(3)
                if not test_mongodb_connection(app):
                    print("❌ Still cannot connect to MongoDB")
                    sys.exit(1)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    
    # Run the application
    print("\n🚀 Starting Nepal Meat Shop...")
    print("🌐 Application will be available at: http://127.0.0.1:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()