
#!/usr/bin/env python3
"""
Database migration script to add new fields to existing tables.
Run this script to update your database schema.
"""

from app import app, db
from models import Order
from sqlalchemy import text, inspect

def migrate_database():
    """Add missing fields to database tables."""
    
    with app.app_context():
        try:
            # Create all tables first (in case they don't exist)
            db.create_all()
            
            # Check if transaction_id column exists in Order table using PostgreSQL syntax
            inspector = inspect(db.engine)
            columns = inspector.get_columns('order')
            column_names = [col['name'] for col in columns]
            
            if 'transaction_id' not in column_names:
                print("Adding transaction_id column to Order table...")
                db.session.execute(text('ALTER TABLE "order" ADD COLUMN transaction_id VARCHAR(100)'))
                db.session.commit()
                print("✅ Added transaction_id column successfully!")
            else:
                print("✅ transaction_id column already exists")
            
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_database()
