
#!/usr/bin/env python3
"""
🛠️ Nepal Meat Shop - Dependency Installation Script
This script installs all required dependencies for the meat shop platform.
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    
    print("✅ Python version is compatible!")
    return True

def install_dependencies():
    """Install all required Python packages."""
    dependencies = [
        "flask>=2.3.0",
        "flask-sqlalchemy>=3.0.0",
        "flask-login>=0.6.0",
        "flask-wtf>=1.1.0",
        "wtforms>=3.0.0",
        "werkzeug>=2.3.0",
        "gunicorn>=20.0.0",
        "pillow>=9.0.0",
        "python-dotenv>=1.0.0"
    ]
    
    print("📦 Installing Python dependencies...")
    
    # Try pip install for each dependency
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def create_directories():
    """Create necessary directories."""
    directories = [
        "uploads",
        "static/uploads",
        "instance"
    ]
    
    print("📁 Creating necessary directories...")
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directory created: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def create_env_file():
    """Create .env file with default configuration."""
    env_content = """# Nepal Meat Shop Environment Configuration
SECRET_KEY=nepal-meat-shop-secret-key-2024
DATABASE_URL=sqlite:///meat_shop.db
FLASK_ENV=development
FLASK_DEBUG=True
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
"""
    
    try:
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                f.write(env_content)
            print("✅ Created .env file with default configuration")
        else:
            print("ℹ️ .env file already exists, skipping creation")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def run_database_setup():
    """Initialize the database."""
    print("🗄️ Setting up database...")
    
    # Try to run the database fix script
    if os.path.exists('fix_database.py'):
        return run_command("python fix_database.py", "Database initialization")
    else:
        # Run basic database setup
        return run_command("python -c \"from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')\"", "Database creation")

def main():
    """Main installation function."""
    print("🚀 Nepal Meat Shop - Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies!")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories!")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("❌ Failed to create environment configuration!")
        sys.exit(1)
    
    # Setup database
    if not run_database_setup():
        print("⚠️ Database setup had issues, but continuing...")
    
    # Final success message
    print("\n" + "=" * 50)
    print("🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. Open browser to: http://localhost:5000")
    print("3. Admin login: admin@meatshop.np / admin123")
    print("\n🔧 For production deployment:")
    print("1. Run: gunicorn --bind 0.0.0.0:5000 main:app")
    print("2. Set proper environment variables")
    print("3. Use a production database (PostgreSQL recommended)")
    print("\n✅ Happy coding! 🍖")

if __name__ == "__main__":
    main()
