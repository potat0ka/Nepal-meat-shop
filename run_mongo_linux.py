#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Application Runner for Linux
Run the Flask application with MongoDB backend on Linux systems.
"""

import os
import sys
import subprocess
import time
import signal
import platform
from mongo_app import create_mongo_app
from app.utils.mongo_db import mongo_db

def get_linux_distro():
    """Get Linux distribution information."""
    try:
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()
            distro_info = {}
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    distro_info[key] = value.strip('"')
            return distro_info.get('ID', 'unknown'), distro_info.get('NAME', 'Unknown Linux')
    except Exception:
        return 'unknown', 'Unknown Linux'

def check_mongodb_installed():
    """Check if MongoDB is installed on Linux."""
    try:
        # Check if mongod is available
        result = subprocess.run(['which', 'mongod'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, None
    except Exception:
        return False, None

def check_mongodb_running():
    """Check if MongoDB service is running on Linux."""
    try:
        # Check systemd service
        result = subprocess.run(['systemctl', 'is-active', 'mongod'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and 'active' in result.stdout:
            return True
        
        # Check if MongoDB process is running
        result = subprocess.run(['pgrep', '-f', 'mongod'], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def start_mongodb_service():
    """Start MongoDB service on Linux."""
    print("🔄 Attempting to start MongoDB service...")
    
    try:
        # Try to start with systemctl
        result = subprocess.run(['sudo', 'systemctl', 'start', 'mongod'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB service started with systemctl")
            time.sleep(3)  # Wait for service to start
            return True
        else:
            print(f"⚠️  systemctl start failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not start with systemctl: {e}")
    
    try:
        # Try to start with service command
        result = subprocess.run(['sudo', 'service', 'mongod', 'start'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB service started with service command")
            time.sleep(3)
            return True
    except Exception as e:
        print(f"⚠️  Could not start with service command: {e}")
    
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

def install_mongodb_linux():
    """Guide user to install MongoDB on Linux."""
    distro_id, distro_name = get_linux_distro()
    
    print(f"\n📦 MongoDB is not installed on your {distro_name} system.")
    print("To install MongoDB, follow these instructions:")
    
    if distro_id in ['ubuntu', 'debian']:
        print("\n🐧 Ubuntu/Debian Installation:")
        print("1. Import MongoDB public GPG key:")
        print("   wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -")
        print("\n2. Add MongoDB repository:")
        print("   echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list")
        print("\n3. Update package database:")
        print("   sudo apt-get update")
        print("\n4. Install MongoDB:")
        print("   sudo apt-get install -y mongodb-org")
        print("\n5. Start MongoDB:")
        print("   sudo systemctl start mongod")
        print("   sudo systemctl enable mongod")
        
    elif distro_id in ['centos', 'rhel', 'fedora']:
        print("\n🎩 CentOS/RHEL/Fedora Installation:")
        print("1. Create MongoDB repository file:")
        print("   sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo << EOF")
        print("   [mongodb-org-7.0]")
        print("   name=MongoDB Repository")
        print("   baseurl=https://repo.mongodb.org/yum/redhat/\\$releasever/mongodb-org/7.0/x86_64/")
        print("   gpgcheck=1")
        print("   enabled=1")
        print("   gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc")
        print("   EOF")
        print("\n2. Install MongoDB:")
        print("   sudo yum install -y mongodb-org")
        print("\n3. Start MongoDB:")
        print("   sudo systemctl start mongod")
        print("   sudo systemctl enable mongod")
        
    elif distro_id == 'arch':
        print("\n🏹 Arch Linux Installation:")
        print("1. Install MongoDB from AUR:")
        print("   yay -S mongodb-bin")
        print("   # or")
        print("   sudo pacman -S mongodb")
        print("\n2. Start MongoDB:")
        print("   sudo systemctl start mongodb")
        print("   sudo systemctl enable mongodb")
    
    else:
        print(f"\n🐧 Generic Linux Installation:")
        print("1. Download MongoDB Community Server from:")
        print("   https://www.mongodb.com/try/download/community")
        print("\n2. Follow the installation guide for your distribution")
    
    print("\n☁️  Alternative: Use MongoDB Atlas (cloud database)")
    print("   Set MONGO_URI environment variable to your Atlas connection string")

def setup_environment():
    """Setup Linux-specific environment variables."""
    # Set default MongoDB URI for Linux
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
        elif 'permission denied' in error_msg:
            print("💡 Permission denied. Check MongoDB data directory permissions.")
            print("   sudo chown -R mongodb:mongodb /var/lib/mongodb")
            print("   sudo chown mongodb:mongodb /tmp/mongodb-27017.sock")
            return False
        else:
            print("💡 Check your MongoDB configuration and try again.")
            return False

def check_system_requirements():
    """Check Linux system requirements."""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 7):
        print(f"⚠️  Python {python_version.major}.{python_version.minor} detected. Python 3.7+ recommended.")
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check available memory
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb < 1:
                        print(f"⚠️  Low memory: {mem_gb:.1f}GB (2GB+ recommended)")
                    else:
                        print(f"✅ Memory: {mem_gb:.1f}GB")
                    break
    except Exception:
        print("⚠️  Could not check memory")
    
    # Check disk space
    try:
        stat = os.statvfs('.')
        free_gb = (stat.f_bavail * stat.f_frsize) / 1024 / 1024 / 1024
        if free_gb < 1:
            print(f"⚠️  Low disk space: {free_gb:.1f}GB")
        else:
            print(f"✅ Free disk space: {free_gb:.1f}GB")
    except Exception:
        print("⚠️  Could not check disk space")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Shutting down Nepal Meat Shop...")
    sys.exit(0)

def main():
    """
    Main function to run the MongoDB application on Linux.
    """
    distro_id, distro_name = get_linux_distro()
    
    print("🍖 Nepal Meat Shop - Linux MongoDB Runner")
    print(f"🐧 Running on: {distro_name}")
    print("=" * 50)
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check system requirements
    check_system_requirements()
    
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
            install_mongodb_linux()
            sys.exit(1)
        
        print(f"✅ MongoDB found at: {mongo_path}")
        
        # Check if MongoDB is running
        if not check_mongodb_running():
            print("⚠️  MongoDB is not running")
            if not start_mongodb_service():
                print("❌ Could not start MongoDB service")
                print("💡 Try starting MongoDB manually:")
                print("   sudo systemctl start mongod")
                print("   or")
                print("   sudo service mongod start")
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