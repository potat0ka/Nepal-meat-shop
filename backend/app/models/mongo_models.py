#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Models
MongoDB document models for users, products, and orders.
"""

from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

class MongoUser(UserMixin):
    """
    MongoDB User model for customer and admin accounts.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.username = data.get('username')
            self.email = data.get('email')
            self.password_hash = data.get('password_hash')
            self.full_name = data.get('full_name')
            self.phone = data.get('phone')
            self.address = data.get('address')
            self.is_admin = data.get('is_admin', False)
            self.is_sub_admin = data.get('is_sub_admin', False)
            self.is_staff = data.get('is_staff', False)
            self._is_active = data.get('is_active', True)
            self.profile_image = data.get('profile_image')
            self.date_joined = data.get('date_joined') or datetime.utcnow()
            self.last_login = data.get('last_login')
            self.reset_token = data.get('reset_token')
            self.reset_token_expiry = data.get('reset_token_expiry')
        else:
            self._id = None
            self.username = None
            self.email = None
            self.password_hash = None
            self.full_name = None
            self.phone = None
            self.address = None
            self.is_admin = False
            self.is_sub_admin = False
            self.is_staff = False
            self._is_active = True
            self.profile_image = None
            self.date_joined = datetime.utcnow()
            self.last_login = None
            self.reset_token = None
            self.reset_token_expiry = None
    
    def get_id(self):
        """Return the user ID as string for Flask-Login."""
        return str(self._id) if self._id else None
    
    @property
    def is_active(self):
        """Return whether the user is active."""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """Set the user's active status."""
        self._is_active = value
    
    @property
    def created_at(self):
        """Return date_joined as created_at for template compatibility."""
        return self.date_joined or datetime.utcnow()
    
    @property
    def orders(self):
        """Return user's orders for template compatibility."""
        if not hasattr(self, '_orders'):
            from app.utils.mongo_db import mongo_db
            if self._id:
                orders_data = list(mongo_db.db.orders.find({'user_id': self._id}))
                self._orders = [MongoOrder(order_data) for order_data in orders_data]
            else:
                self._orders = []
        return self._orders
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    # Role-based permission methods
    def has_admin_access(self):
        """Check if user has admin access (admin or sub-admin)."""
        return self.is_admin or self.is_sub_admin
    
    def has_staff_access(self):
        """Check if user has staff access (admin, sub-admin, or staff)."""
        return self.is_admin or self.is_sub_admin or self.is_staff
    
    def can_manage_orders(self):
        """Check if user can manage orders (admin, sub-admin, or staff)."""
        return self.is_admin or self.is_sub_admin or self.is_staff
    
    def can_confirm_orders(self):
        """Check if user can confirm orders (admin, sub-admin, or staff)."""
        return self.is_admin or self.is_sub_admin or self.is_staff
    
    def can_update_delivery_status(self):
        """Check if user can update delivery status (admin, sub-admin, or staff)."""
        return self.is_admin or self.is_sub_admin or self.is_staff
    
    def can_manage_users(self):
        """Check if user can manage other users (admin only)."""
        return self.is_admin
    
    def can_grant_roles(self):
        """Check if user can grant/revoke roles (admin only)."""
        return self.is_admin
    
    def can_grant_staff_role(self):
        """Check if user can grant/revoke staff role (admin and sub-admin)."""
        return self.is_admin or self.is_sub_admin
    
    def can_edit_user(self, target_user):
        """Check if user can edit another user's details."""
        if self.is_admin:
            # Admin can edit all users except cannot demote other admins
            return True
        elif self.is_sub_admin:
            # Sub-admin cannot edit other users' details
            return False
        else:
            # Customer can only edit their own details
            return str(self._id) == str(target_user._id)
    
    def can_promote_to_sub_admin(self, target_user):
        """Check if user can promote another user to sub-admin."""
        return self.is_admin and not target_user.is_admin and not target_user.is_sub_admin
    
    def can_demote_from_sub_admin(self, target_user):
        """Check if user can demote a sub-admin (admin cannot demote sub-admins per requirements)."""
        return False  # Per requirements: admin cannot demote sub-admins
    
    def to_dict(self):
        """Convert user object to dictionary for MongoDB storage."""
        data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'is_admin': self.is_admin,
            'is_sub_admin': self.is_sub_admin,
            'is_staff': self.is_staff,
            'is_active': self.is_active,
            'profile_image': self.profile_image,
            'date_joined': self.date_joined,
            'last_login': self.last_login,
            'reset_token': self.reset_token,
            'reset_token_expiry': self.reset_token_expiry
        }
        if self._id is not None:
            data['_id'] = self._id
        return data

class MongoProduct:
    """
    MongoDB Product model for meat items.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.name = data.get('name')
            self.name_nepali = data.get('name_nepali')
            self.description = data.get('description')
            self.price = data.get('price')
            self.image_url = data.get('image_url')
            self.category = data.get('category')
            self.category_id = data.get('category_id')
            self.meat_type = data.get('meat_type')
            self.preparation_type = data.get('preparation_type', 'fresh')
            self.stock_quantity = data.get('stock_quantity', 0)
            self.unit = data.get('unit', 'kg')
            self.is_featured = data.get('is_featured', False)
            self.is_available = data.get('is_available', True)
            self.date_added = data.get('date_added') or datetime.utcnow()
            self.last_updated = data.get('last_updated', datetime.utcnow())
            # Additional attributes for compatibility
            self.min_order_kg = data.get('min_order_kg', 0.5)
            self.freshness_hours = data.get('freshness_hours', 24)
            self.cooking_tips = data.get('cooking_tips')
        else:
            self._id = None
            self.name = None
            self.name_nepali = None
            self.description = None
            self.price = None
            self.image_url = None
            self.category = None
            self.category_id = None
            self.meat_type = None
            self.preparation_type = 'fresh'
            self.stock_quantity = 0
            self.unit = 'kg'
            self.is_featured = False
            self.is_available = True
            self.date_added = datetime.utcnow()
            self.last_updated = datetime.utcnow()
            # Additional attributes for compatibility
            self.min_order_kg = 0.5
            self.freshness_hours = 24
            self.cooking_tips = None
    
    @property
    def id(self):
        """Return _id as id for template compatibility."""
        return str(self._id) if self._id else None
    
    @property
    def stock_kg(self):
        """Return stock_quantity as stock_kg for compatibility."""
        return self.stock_quantity
    
    @stock_kg.setter
    def stock_kg(self, value):
        """Set stock_quantity when stock_kg is assigned."""
        self.stock_quantity = value
    
    @property
    def created_at(self):
        """Return date_added as created_at for template compatibility."""
        return self.date_added or datetime.utcnow()
    
    def get_freshness_label(self):
        """Get freshness label based on processing hours."""
        if self.freshness_hours <= 6:
            return "आज ताजा / Fresh Today"
        elif self.freshness_hours <= 24:
            return "हिजो काटिएको / Cut Yesterday"
        else:
            return "स्टक / Stock"
    
    def is_in_stock(self, quantity_kg):
        """Check if requested quantity is available in stock."""
        return self.stock_kg >= quantity_kg
    
    def get_average_rating(self):
        """Calculate average rating from customer reviews."""
        # For now, return 0 as reviews are not implemented in MongoDB version
        return 0
    
    def to_dict(self):
        """Convert product object to dictionary for MongoDB storage."""
        data = {
            'name': self.name,
            'name_nepali': self.name_nepali,
            'description': self.description,
            'price': self.price,
            'image_url': self.image_url,
            'category': self.category,
            'category_id': self.category_id,
            'meat_type': self.meat_type,
            'preparation_type': self.preparation_type,
            'stock_quantity': self.stock_quantity,
            'unit': self.unit,
            'is_featured': self.is_featured,
            'is_available': self.is_available,
            'date_added': self.date_added,
            'last_updated': self.last_updated,
            'min_order_kg': self.min_order_kg,
            'freshness_hours': self.freshness_hours,
            'cooking_tips': self.cooking_tips
        }
        if self._id is not None:
            data['_id'] = self._id
        return data

class MongoOrderItem:
    """
    MongoDB Order Item wrapper to provide product object compatibility.
    """
    
    def __init__(self, item_data):
        self.product_id = item_data.get('product_id')
        self.product_name = item_data.get('product_name', 'Unknown Product')
        self.quantity = item_data.get('quantity', 0) or 0  # Handle None values
        self.unit_price = item_data.get('unit_price', 0) or 0  # Handle None values
        self.total_price = item_data.get('total_price', 0) or 0  # Handle None values
        self._product = None  # Cache for product data
    
    @property
    def product(self):
        """Get product data for this order item."""
        if self._product is None and self.product_id:
            from app.utils.mongo_db import mongo_db
            try:
                product_data = mongo_db.find_product_by_id(self.product_id)
                if product_data:
                    self._product = product_data
                else:
                    # Create a minimal product object if product not found
                    self._product = type('Product', (), {
                        'name': self.product_name,
                        'name_nepali': self.product_name,
                        'image_url': None,
                        'description': '',
                        'meat_type': '',
                        'category': type('Category', (), {'name': ''})(),
                        'price': self.unit_price
                    })()
            except Exception as e:
                print(f"Error loading product for order item {self.product_id}: {e}")
                # Create a minimal product object as fallback
                self._product = type('Product', (), {
                    'name': self.product_name,
                    'name_nepali': self.product_name,
                    'image_url': None,
                    'description': '',
                    'meat_type': '',
                    'category': type('Category', (), {'name': ''})(),
                    'price': self.unit_price
                })()
        return self._product

class MongoOrder:
    """
    MongoDB Order model for customer purchases.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.order_number = data.get('order_number')
            self.user_id = data.get('user_id')
            self.items = data.get('items', [])
            self.total_amount = data.get('total_amount', 0) or 0  # Handle None values
            self.status = data.get('status', 'pending')
            self.delivery_address = data.get('delivery_address')
            self.delivery_latitude = data.get('delivery_latitude')
            self.delivery_longitude = data.get('delivery_longitude')
            self.delivery_formatted_address = data.get('delivery_formatted_address')
            self.phone_number = data.get('phone_number')
            self.payment_method = data.get('payment_method')
            self.payment_status = data.get('payment_status', 'pending')
            self.order_date = data.get('order_date') or datetime.utcnow()
            self.delivery_date = data.get('delivery_date')
            self.estimated_delivery = data.get('estimated_delivery')
            self.transaction_id = data.get('transaction_id')
            self.notes = data.get('notes')
            self.special_instructions = data.get('special_instructions')
            self._user = None  # Cache for user data
            self._order_items = None  # Cache for order items with product objects
        else:
            self._id = None
            self.order_number = None
            self.user_id = None
            self.items = []
            self.total_amount = None
            self.status = 'pending'
            self.delivery_address = None
            self.delivery_latitude = None
            self.delivery_longitude = None
            self.delivery_formatted_address = None
            self.phone_number = None
            self.payment_method = None
            self.payment_status = 'pending'
            self.order_date = datetime.utcnow()
            self.delivery_date = None
            self.estimated_delivery = None
            self.transaction_id = None
            self.notes = None
            self.special_instructions = None
            self._user = None
            self._order_items = None
    
    @property
    def created_at(self):
        """Return order_date as created_at for template compatibility."""
        return self.order_date or datetime.utcnow()
    
    @property
    def delivery_phone(self):
        """Return phone_number as delivery_phone for template compatibility."""
        return self.phone_number
    
    @property
    def formatted_delivery_address(self):
        """Return properly formatted delivery address for display."""
        if not self.delivery_address:
            return 'N/A'
        
        if isinstance(self.delivery_address, dict):
            # Extract address components from dictionary
            full_name = self.delivery_address.get('full_name', '')
            address = self.delivery_address.get('address', '')
            city = self.delivery_address.get('city', '')
            postal_code = self.delivery_address.get('postal_code', '')
            
            # Build formatted address
            address_parts = []
            if full_name:
                address_parts.append(f"Name: {full_name}")
            if address:
                address_parts.append(f"Address: {address}")
            if city:
                address_parts.append(f"City: {city}")
            if postal_code:
                address_parts.append(f"Postal Code: {postal_code}")
            
            return '\n'.join(address_parts) if address_parts else 'N/A'
        
        elif isinstance(self.delivery_address, str):
            return self.delivery_address.strip() if self.delivery_address.strip() else 'N/A'
        
        else:
            return str(self.delivery_address) if self.delivery_address else 'N/A'
    
    @property
    def order_items(self):
        """Return items as order_items with product objects for template compatibility."""
        if self._order_items is None:
            self._order_items = [MongoOrderItem(item_data) for item_data in self.items]
        return self._order_items
    
    @property
    def user(self):
        """Get user data for this order."""
        if self._user is None and self.user_id:
            from app.utils.mongo_db import mongo_db
            from bson import ObjectId
            try:
                user_data = mongo_db.db.users.find_one({'_id': ObjectId(self.user_id)})
                if user_data:
                    self._user = MongoUser(user_data)
            except Exception as e:
                print(f"Error loading user for order {self._id}: {e}")
                self._user = None
        return self._user
    
    def to_dict(self):
        """Convert order object to dictionary for MongoDB storage."""
        data = {
            'order_number': self.order_number,
            'user_id': self.user_id,
            'items': self.items,
            'total_amount': self.total_amount,
            'status': self.status,
            'delivery_address': self.delivery_address,
            'delivery_latitude': self.delivery_latitude,
            'delivery_longitude': self.delivery_longitude,
            'delivery_formatted_address': self.delivery_formatted_address,
            'phone_number': self.phone_number,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'order_date': self.order_date,
            'delivery_date': self.delivery_date,
            'estimated_delivery': self.estimated_delivery,
            'transaction_id': self.transaction_id,
            'notes': self.notes,
            'special_instructions': self.special_instructions
        }
        if self._id is not None:
            data['_id'] = self._id
        return data
    
    def to_json_dict(self):
        """Convert order object to JSON-serializable dictionary for templates."""
        # Get user info
        user_info = self.user
        customer_name = user_info.full_name if user_info else 'Unknown Customer'
        customer_phone = user_info.phone if user_info else self.phone_number
        
        # Format delivery address
        delivery_area = 'Unknown'
        if isinstance(self.delivery_address, dict):
            delivery_area = self.delivery_address.get('area', 'Unknown')
        elif isinstance(self.delivery_address, str):
            delivery_area = self.delivery_address if self.delivery_address.strip() else 'Unknown'
        
        # Keep dates as datetime objects for template strftime usage
        # Provide fallback datetime if dates are None
        from datetime import datetime
        order_date = self.order_date if self.order_date else datetime.utcnow()
        delivery_date = self.delivery_date if self.delivery_date else None
        
        return {
            'order_id': str(self._id) if self._id else '',
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'order_date': order_date,
            'delivery_date': delivery_date,
            'status': self.status,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'delivery_area': delivery_area,
            'payment_method': self.payment_method or 'Not specified',
            'payment_status': self.payment_status,
            'notes': self.notes or '',
            'special_instructions': self.special_instructions or '',
            'items_count': len(self.items),
            'order_type': 'Online' if self.payment_method else 'Phone'
        }

class MongoCategory:
    """
    MongoDB Category model for product categories.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.name = data.get('name')
            self.name_nepali = data.get('name_nepali')
            self.description = data.get('description')
            self.image_url = data.get('image_url')
            self.is_active = data.get('is_active', True)
            self.sort_order = data.get('sort_order', 0)
        else:
            self._id = None
            self.name = None
            self.name_nepali = None
            self.description = None
            self.image_url = None
            self.is_active = True
            self.sort_order = 0
    
    def to_dict(self):
        """Convert category object to dictionary for MongoDB storage."""
        data = {
            'name': self.name,
            'name_nepali': self.name_nepali,
            'description': self.description,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }
        if self._id is not None:
            data['_id'] = self._id
        return data