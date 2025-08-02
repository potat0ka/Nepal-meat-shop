
"""
Quick Database Fix Script
Run this if you encounter database errors
"""

from database import init_database, show_admin_credentials, check_database_status
import sys

def main():
    print("🔧 Database Fix Utility")
    print("This will reinitialize your database and fix common issues")
    print("")
    
    try:
        # Initialize database
        init_database()
        
        # Show credentials
        show_admin_credentials()
        
        # Check status
        print("\n🔍 Final Database Check:")
        check_database_status()
        
        print("\n🎉 Database has been fixed successfully!")
        print("You can now run your application and login with the admin credentials above.")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        print("Please check your database configuration in app.py")
        sys.exit(1)

if __name__ == '__main__':
    main()
