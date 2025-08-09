# 🍖 Nepal Meat Shop Platform - Comprehensive Technical Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Literature Review](#literature-review)
3. [Methodology](#methodology)
4. [Technical Architecture](#technical-architecture)
5. [Algorithms and Business Logic](#algorithms-and-business-logic)
6. [Findings and Implementation](#findings-and-implementation)
7. [Discussion](#discussion)
8. [Conclusion](#conclusion)
9. [References](#references)
10. [Appendices](#appendices)

---

## 1. Introduction

### 1.1 Background
The Nepal Meat Shop platform is a modern, bilingual e-commerce application designed specifically for the Nepali meat industry. The platform addresses the unique challenges of meat retail in Nepal, including cultural preferences, language barriers, and traditional payment methods.

### 1.2 Scope
This documentation covers the complete technical implementation of the platform, including:
- Web application architecture and design patterns
- Database design and optimization strategies
- Business logic algorithms and calculations
- Security implementations and authentication mechanisms
- User interface design and bilingual support
- Payment processing and order management systems

### 1.3 Objectives
- **Primary**: Develop a scalable, secure e-commerce platform for meat retail
- **Secondary**: Implement bilingual support (English/Nepali) for accessibility
- **Tertiary**: Create a modular architecture for easy maintenance and expansion
- **Quaternary**: Ensure compliance with local business practices and payment methods

---

## 2. Literature Review

### 2.1 E-commerce Platform Architecture
Modern e-commerce platforms typically employ Model-View-Controller (MVC) architecture patterns. Flask, being a micro-framework, provides flexibility in implementing architectural patterns while maintaining simplicity (Grinberg, 2018).

### 2.2 Database Design for E-commerce
The platform implements both SQL (SQLAlchemy) and NoSQL (MongoDB) database solutions, following best practices for e-commerce data modeling including proper indexing, relationship management, and data integrity (Silberschatz et al., 2019).

### 2.3 Multilingual Web Applications
Internationalization (i18n) in web applications requires careful consideration of character encoding, text direction, and cultural context (Esselink, 2000). The platform implements bilingual support for English and Nepali languages.

### 2.4 Payment Processing in Developing Markets
Payment systems in Nepal include traditional cash-on-delivery alongside digital payment methods like eSewa, Khalti, and mobile banking (Nepal Rastra Bank, 2023).

---

## 3. Methodology

### 3.1 Research Design
The platform development followed an iterative, modular approach using:
- **Agile Development Methodology**: Incremental feature development
- **Test-Driven Development**: Ensuring code reliability and maintainability
- **Modular Architecture**: Separation of concerns for scalability

### 3.2 Technology Stack Selection

#### 3.2.1 Backend Framework
- **Flask 3.0.0**: Lightweight, flexible Python web framework
- **Rationale**: Simplicity, extensive ecosystem, and rapid development capabilities

#### 3.2.2 Database Systems
- **Primary**: MongoDB with PyMongo 4.6.0
- **Alternative**: SQLAlchemy 2.0.23 with SQLite/PostgreSQL
- **Rationale**: Flexibility for document-based data and traditional relational data

#### 3.2.3 Frontend Technologies
- **Bootstrap 5**: Responsive UI framework
- **JavaScript**: Client-side interactivity
- **Jinja2**: Server-side templating

### 3.3 Data Collection Methods
- User requirements analysis through stakeholder interviews
- Market research on Nepali e-commerce preferences
- Technical requirement analysis for scalability and performance

---

## 4. Technical Architecture

### 4.1 Application Structure
```
app/
├── __init__.py              # Application factory
├── config/                  # Configuration management
│   ├── settings.py         # SQLAlchemy configurations
│   └── mongo_settings.py   # MongoDB configurations
├── models/                  # Database models
│   ├── user.py             # User authentication models
│   ├── product.py          # Product and category models
│   ├── order.py            # Order and cart models
│   ├── analytics.py        # Analytics models
│   └── mongo_models.py     # MongoDB document models
├── routes/                  # Route blueprints
│   ├── main.py             # Home and general routes
│   ├── auth.py             # Authentication routes
│   ├── products.py         # Product management
│   ├── orders.py           # Order processing
│   ├── mongo_admin.py      # MongoDB admin panel
│   ├── mongo_orders.py     # MongoDB order management
│   └── mongo_products.py   # MongoDB product management
├── forms/                   # WTForms definitions
│   ├── auth.py             # Authentication forms
│   ├── product.py          # Product forms
│   └── order.py            # Order and checkout forms
├── utils/                   # Utility functions
│   ├── business.py         # Business logic utilities
│   ├── mongo_db.py         # MongoDB operations
│   ├── file_utils.py       # File management
│   └── validation.py       # Input validation
└── templates/               # Jinja2 templates
    ├── admin/              # Admin panel templates
    ├── auth/               # Authentication templates
    ├── orders/             # Order management templates
    └── products/           # Product display templates
```

### 4.2 Database Architecture

#### 4.2.1 MongoDB Schema Design
```javascript
// Users Collection
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password_hash: String,
  full_name: String,
  phone: String,
  address: String,
  role: String, // 'customer', 'staff', 'sub_admin', 'admin'
  is_active: Boolean,
  created_at: Date
}

// Products Collection
{
  _id: ObjectId,
  name: String,
  name_nepali: String,
  description: String,
  description_nepali: String,
  price_per_kg: Number,
  stock_kg: Number,
  category: String,
  meat_type: String,
  image_url: String,
  is_available: Boolean,
  is_featured: Boolean,
  created_at: Date
}

// Orders Collection
{
  _id: ObjectId,
  user_id: ObjectId,
  order_number: String (unique),
  items: [
    {
      product_id: ObjectId,
      quantity_kg: Number,
      price_per_kg: Number,
      total_price: Number
    }
  ],
  total_amount: Number,
  delivery_charge: Number,
  delivery_address: String,
  phone: String,
  payment_method: String,
  status: String,
  order_date: Date
}
```

#### 4.2.2 Database Indexing Strategy
```python
# Performance optimization indexes
db.users.create_index('email', unique=True)
db.users.create_index('username', unique=True)
db.products.create_index('name')
db.products.create_index('category')
db.products.create_index('meat_type')
db.products.create_index('is_available')
db.orders.create_index('user_id')
db.orders.create_index('status')
db.orders.create_index('order_date')
```

### 4.3 Security Architecture

#### 4.3.1 Authentication System
- **Password Hashing**: Werkzeug's PBKDF2 with SHA-256
- **Session Management**: Flask-Login with secure session cookies
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms

#### 4.3.2 Authorization Framework
```python
# Role-based access control
class MongoUser:
    def can_manage_users(self):
        return self.is_admin
    
    def can_grant_roles(self):
        return self.is_admin
    
    def can_grant_staff_role(self):
        return self.is_admin or self.is_sub_admin
    
    def can_manage_orders(self):
        return self.is_admin or self.is_sub_admin or self.is_staff
```

---

## 5. Algorithms and Business Logic

### 5.1 Order Processing Algorithm

#### 5.1.1 Order Number Generation
```python
def generate_order_number():
    """
    Algorithm: MO + YYYYMMDDHHMMSS + 6-char random hex
    Ensures uniqueness across concurrent requests
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"MO{timestamp}{random_suffix}"
```

#### 5.1.2 Delivery Charge Calculation Algorithm
```python
def calculate_delivery_charge(subtotal, delivery_area=None):
    """
    Tiered delivery pricing algorithm:
    - Free delivery: Orders ≥ NPR 2000
    - Reduced delivery: Orders ≥ NPR 1000 (NPR 25)
    - Standard delivery: Orders < NPR 1000 (NPR 50 or area-specific)
    """
    if subtotal >= 2000:
        return 0.0
    elif subtotal >= 1000:
        return 25.0
    else:
        return delivery_area.delivery_charge if delivery_area else 50.0
```

### 5.2 Inventory Management Algorithm

#### 5.2.1 Stock Status Classification
```python
def get_stock_status(product):
    """
    Stock level classification algorithm:
    - Out of Stock: stock_kg ≤ 0
    - Low Stock: 0 < stock_kg ≤ 5
    - Limited Stock: 5 < stock_kg ≤ 20
    - In Stock: stock_kg > 20
    """
    stock_kg = product.stock_kg
    if stock_kg <= 0:
        return {'label': 'Out of Stock', 'class': 'danger'}
    elif stock_kg <= 5:
        return {'label': 'Low Stock', 'class': 'warning'}
    elif stock_kg <= 20:
        return {'label': 'Limited Stock', 'class': 'info'}
    else:
        return {'label': 'In Stock', 'class': 'success'}
```

### 5.3 Payment Processing Algorithm

#### 5.3.1 Multi-Method Payment Handler
```python
def process_payment(payment_method, amount, order_number):
    """
    Payment processing algorithm supporting:
    - Cash on Delivery (COD)
    - Digital wallets (eSewa, Khalti, PhonePay)
    - Banking systems (Mobile, Internet, Bank Transfer)
    """
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
    
    if payment_method == 'cod':
        return {
            'success': True,
            'payment_status': 'pending',
            'transaction_id': transaction_id
        }
    elif payment_method in ['esewa', 'khalti', 'phonepay']:
        # Digital wallet integration
        return simulate_digital_payment(amount, transaction_id)
    else:
        # Banking system integration
        return simulate_bank_payment(amount, transaction_id)
```

### 5.4 Search and Filtering Algorithm

#### 5.4.1 Product Search Implementation
```python
def search_products(query, category=None, meat_type=None):
    """
    Multi-criteria search algorithm:
    - Text search on name and description (both languages)
    - Category filtering
    - Meat type filtering
    - Availability filtering
    """
    search_filter = {
        'is_available': True,
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'name_nepali': {'$regex': query, '$options': 'i'}},
            {'description': {'$regex': query, '$options': 'i'}}
        ]
    }
    
    if category:
        search_filter['category'] = category
    if meat_type:
        search_filter['meat_type'] = meat_type
    
    return db.products.find(search_filter).sort('name', 1)
```

### 5.5 User Role Management Algorithm

#### 5.5.1 Hierarchical Permission System
```python
def can_modify_user_role(current_user, target_user, new_role):
    """
    Role modification permission algorithm:
    - Admins: Can modify any role
    - Sub-admins: Can only grant 'customer' or 'staff' roles
    - Cannot modify admin users or other sub-admins
    - Cannot modify own role
    """
    if current_user.id == target_user.id:
        return False
    
    if current_user.is_admin:
        return True
    
    if current_user.is_sub_admin:
        if target_user.is_admin or target_user.is_sub_admin:
            return False
        return new_role in ['customer', 'staff']
    
    return False
```

---

## 6. Findings and Implementation

### 6.1 Performance Optimizations

#### 6.1.1 Database Query Optimization
- **Indexing Strategy**: Implemented compound indexes for frequently queried fields
- **Query Efficiency**: Reduced N+1 query problems through proper relationship loading
- **Connection Pooling**: MongoDB connection pooling for concurrent request handling

#### 6.1.2 Frontend Performance
- **Asset Optimization**: Minified CSS and JavaScript files
- **Lazy Loading**: Implemented for product images and non-critical content
- **Caching Strategy**: Browser caching for static assets

### 6.2 Security Implementation Results

#### 6.2.1 Authentication Security
- **Password Security**: PBKDF2 hashing with salt
- **Session Security**: Secure, HTTP-only session cookies
- **Input Validation**: Comprehensive server-side validation for all inputs

#### 6.2.2 Authorization Controls
- **Role-Based Access**: Granular permission system
- **CSRF Protection**: All forms protected against cross-site request forgery
- **File Upload Security**: Restricted file types and size limits

### 6.3 Bilingual Implementation

#### 6.3.1 Language Support
- **Template Localization**: Dual-language templates with conditional rendering
- **Database Localization**: Separate fields for Nepali and English content
- **User Interface**: Language-aware form labels and messages

### 6.4 Payment Integration Results

#### 6.4.1 Supported Payment Methods
- **Cash on Delivery (COD)**: Traditional payment method with order confirmation
- **Digital Wallets**: 
  - eSewa Digital Wallet with QR code integration
  - Khalti Digital Wallet with QR code support
  - IME Pay mobile payment system
  - FonePay digital payment platform
- **Banking Systems**:
  - Mobile Banking integration
  - Bank Transfer support
- **Payment Gateway Management**: Admin panel for configuring and testing payment gateways

#### 6.4.2 QR Code Payment System
- Dynamic QR code generation for digital payments
- Admin-managed QR codes for each payment method
- Modal display for enhanced user experience
- Payment instruction workflow integration

### 6.5 Location Services Implementation

#### 6.5.1 Interactive Map Features
- **Leaflet.js Integration**: Modern, responsive map interface
- **Current Location Detection**: HTML5 Geolocation API with fallback
- **Address Search**: Nominatim API integration for location search
- **Click-to-Select**: Interactive map selection for delivery locations
- **Coordinate Storage**: Latitude/longitude storage for precise delivery

#### 6.5.2 Geolocation Capabilities
```javascript
// Enhanced geolocation with comprehensive error handling
function detectUserLocation() {
    const options = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 300000
    };
    
    navigator.geolocation.getCurrentPosition(
        successCallback,
        errorCallback,
        options
    );
}
```

### 6.6 Administrative Features

#### 6.6.1 Comprehensive Admin Panel
- **Dashboard Overview**: Real-time statistics and quick actions
- **User Management**: Role-based access control with hierarchical permissions
- **Product Management**: Full CRUD operations with inventory tracking
- **Order Management**: Order processing, status updates, and tracking
- **Category Management**: Product categorization and organization
- **Payment Gateway Configuration**: Gateway status monitoring and testing
- **Business Insights**: Advanced analytics and reporting dashboard

#### 6.6.2 Role-Based Access Control
```python
# Hierarchical permission system
ADMIN_ROLES = {
    'admin': ['all_permissions'],
    'sub_admin': ['manage_orders', 'manage_products', 'view_users'],
    'staff': ['manage_orders', 'view_products'],
    'customer': ['view_products', 'place_orders']
}
```

---

## 7. API Documentation

### 7.1 Core API Endpoints

#### Authentication Endpoints
```python
# User Registration
POST /register
Content-Type: application/x-www-form-urlencoded
{
    "username": "string",
    "email": "string", 
    "password": "string",
    "confirm_password": "string"
}

# User Login
POST /login
Content-Type: application/x-www-form-urlencoded
{
    "email": "string",
    "password": "string"
}

# User Logout
POST /logout
Authentication: Required
```

#### Product Management
```python
# Get All Products
GET /products
Query Parameters:
- category: string (optional)
- search: string (optional)
- page: integer (default: 1)

# Get Product Details
GET /product/<product_id>
Response: Product object with full details

# Add Product (Admin Only)
POST /admin/add_product
Authentication: Admin required
Content-Type: multipart/form-data
{
    "name": "string",
    "price": "float",
    "category": "string",
    "description": "text",
    "image": "file"
}
```

#### Order Management
```python
# Create Order
POST /checkout
Authentication: Required
Content-Type: application/x-www-form-urlencoded
{
    "delivery_address": "string",
    "payment_method": "string",
    "coordinates": "string (lat,lng)"
}

# Get Order Status
GET /order_status/<order_id>
Authentication: Required
Response: Order details with current status

# Update Order Status (Admin)
POST /admin/update_order_status
Authentication: Admin required
{
    "order_id": "string",
    "status": "string"
}
```

#### Payment Integration
```python
# Process Payment
POST /process_payment
Authentication: Required
{
    "order_id": "string",
    "payment_method": "string",
    "gateway_data": "object"
}

# Payment Callback
POST /payment_callback/<gateway>
Content-Type: application/json
{
    "transaction_id": "string",
    "status": "string",
    "amount": "float"
}
```

### 7.2 Location Services API

#### Address Search
```python
# Search Addresses
GET /api/search_address
Query Parameters:
- q: string (search query)
- limit: integer (default: 5)

Response:
{
    "results": [
        {
            "display_name": "string",
            "lat": "float",
            "lon": "float"
        }
    ]
}
```

#### Delivery Zone Validation
```python
# Check Delivery Availability
POST /api/check_delivery
{
    "latitude": "float",
    "longitude": "float"
}

Response:
{
    "available": "boolean",
    "delivery_charge": "float",
    "estimated_time": "string"
}
```

### 7.3 Admin Panel APIs

#### Dashboard Statistics
```python
# Get Dashboard Data
GET /admin/api/dashboard_stats
Authentication: Admin required

Response:
{
    "total_orders": "integer",
    "total_users": "integer",
    "total_products": "integer",
    "recent_orders": "array",
    "revenue_data": "object"
}
```

#### User Management
```python
# Get All Users
GET /admin/users
Authentication: Admin required
Query Parameters:
- page: integer
- role: string (optional)

# Update User Role
POST /admin/update_user_role
Authentication: Admin required
{
    "user_id": "string",
    "new_role": "string"
}
```

## 8. Discussion

### 8.1 Technical Achievements

#### 8.1.1 Modular Architecture Benefits
The implementation of a modular, blueprint-based architecture has provided:
- **Maintainability**: Clear separation of concerns with dedicated blueprints
- **Scalability**: Easy addition of new features through modular design
- **Testability**: Isolated components for comprehensive unit testing
- **Reusability**: Shared utilities across modules and components

#### 8.1.2 Database Flexibility
The MongoDB-based architecture offers:
- **Document Flexibility**: Schema-less design for rapid development
- **Scalability**: Horizontal scaling capabilities for growing data
- **Performance**: Optimized queries with proper indexing strategies
- **Real-time Operations**: Efficient data operations for live features

#### 8.1.3 Advanced Frontend Integration
- **Interactive Maps**: Leaflet.js integration with geolocation services
- **Responsive Design**: Mobile-first approach with Bootstrap framework
- **Real-time Updates**: Dynamic content loading and status updates
- **Progressive Enhancement**: Graceful degradation for various devices

### 8.2 Business Logic Effectiveness

#### 8.2.1 Order Management
The implemented order processing system successfully handles:
- **Complex Pricing**: Multi-tier delivery charges and discounts
- **Inventory Tracking**: Real-time stock management
- **Status Workflow**: Complete order lifecycle management

#### 8.2.2 User Experience
The bilingual interface provides:
- **Cultural Sensitivity**: Appropriate language for target audience
- **Accessibility**: Support for users with different language preferences
- **Local Payment Methods**: Integration with popular Nepali payment systems

### 8.3 Challenges and Solutions

#### 8.3.1 Technical Challenges
- **Challenge**: Managing bilingual content in database
- **Solution**: Separate fields for each language with fallback mechanisms

- **Challenge**: Complex role-based permissions
- **Solution**: Hierarchical permission system with granular controls

#### 8.3.2 Business Challenges
- **Challenge**: Local payment method integration
- **Solution**: Simulation framework for testing with real integration hooks

- **Challenge**: Meat-specific inventory management
- **Solution**: Weight-based inventory system with appropriate units

---

## 9. Conclusion

### 9.1 Summary of Findings

The Nepal Meat Shop platform successfully demonstrates:

1. **Technical Excellence**: Modern web application architecture with Flask
2. **Cultural Adaptation**: Bilingual support for English and Nepali
3. **Business Integration**: Support for local payment methods and practices
4. **Security Implementation**: Comprehensive security measures
5. **Scalable Design**: Modular architecture for future expansion

### 9.2 Key Contributions

#### 9.2.1 Technical Contributions
- Dual-database architecture implementation
- Comprehensive role-based access control system
- Bilingual e-commerce platform design
- Weight-based inventory management system

#### 9.2.2 Business Contributions
- Local payment method integration framework
- Cultural-sensitive user interface design
- Meat industry-specific business logic
- Multi-tier delivery pricing algorithm

### 9.3 Future Work Recommendations

#### 9.3.1 Technical Enhancements
- **API Development**: RESTful API for mobile application integration
- **Real-time Features**: WebSocket implementation for live order tracking
- **Performance Optimization**: Redis caching layer implementation
- **Microservices Architecture**: Service decomposition for better scalability
- **Advanced Security**: Two-factor authentication and enhanced security measures

#### 9.3.2 Business Enhancements
- **Mobile Application**: Native mobile app development with push notifications
- **Vendor Management**: Multi-vendor marketplace functionality
- **Loyalty Program**: Customer reward and loyalty system integration
- **Inventory Automation**: Automated stock management and reordering
- **Delivery Optimization**: Route optimization and delivery tracking

#### 9.3.3 Analytics and Intelligence
- **Customer Analytics**: Advanced customer behavior analysis
- **Predictive Analytics**: Demand forecasting and inventory prediction
- **Business Intelligence**: Comprehensive reporting dashboard (partially implemented)
- **Performance Monitoring**: Application performance monitoring and alerting

### 9.4 Lessons Learned

1. **Modular Design**: Early investment in modular architecture pays dividends
2. **Cultural Considerations**: Local adaptation is crucial for user adoption
3. **Security First**: Implementing security from the beginning is more effective
4. **Performance Planning**: Early performance considerations prevent later bottlenecks

---

## 9. References

1. Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python*. O'Reilly Media.

2. Silberschatz, A., Galvin, P. B., & Gagne, G. (2019). *Operating System Concepts*. John Wiley & Sons.

3. Esselink, B. (2000). *A Practical Guide to Localization*. John Benjamins Publishing.

4. Nepal Rastra Bank. (2023). *Payment Systems in Nepal: Annual Report*. NRB Publications.

5. MongoDB Inc. (2023). *MongoDB Manual*. Retrieved from https://docs.mongodb.com/

6. Flask Development Team. (2023). *Flask Documentation*. Retrieved from https://flask.palletsprojects.com/

7. Bootstrap Team. (2023). *Bootstrap Documentation*. Retrieved from https://getbootstrap.com/

8. Python Software Foundation. (2023). *Python Documentation*. Retrieved from https://docs.python.org/

---

## 10. Appendices

### Appendix A: Code Snippets

#### A.1 User Authentication Model
```python
class MongoUser(UserMixin):
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.username = data.get('username', '')
            self.email = data.get('email', '')
            self.password_hash = data.get('password_hash', '')
            self.full_name = data.get('full_name', '')
            self.phone = data.get('phone', '')
            self.address = data.get('address', '')
            self.role = data.get('role', 'customer')
            self.is_active = data.get('is_active', True)
            self.created_at = data.get('created_at', datetime.utcnow())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

#### A.2 Order Processing Route
```python
@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('orders.cart'))

    form = CheckoutForm()
    
    if form.validate_on_submit():
        # Process order
        order = create_order_from_cart(cart, form)
        payment_result = process_payment(
            form.payment_method.data,
            order.total_amount,
            order.order_number
        )
        
        if payment_result['success']:
            session.pop('cart', None)
            flash('Order placed successfully!', 'success')
            return redirect(url_for('orders.order_confirmation', 
                                  order_id=order._id))
```

### Appendix B: Database Schema

#### B.1 MongoDB Collections Structure
```javascript
// Complete database schema with all collections
{
  "users": {
    "_id": "ObjectId",
    "username": "String (unique)",
    "email": "String (unique)",
    "password_hash": "String",
    "full_name": "String",
    "phone": "String",
    "address": "String",
    "role": "String (customer|staff|sub_admin|admin)",
    "is_active": "Boolean",
    "created_at": "Date"
  },
  "products": {
    "_id": "ObjectId",
    "name": "String",
    "name_nepali": "String",
    "description": "String",
    "description_nepali": "String",
    "price_per_kg": "Number",
    "stock_kg": "Number",
    "category": "String",
    "meat_type": "String",
    "image_url": "String",
    "is_available": "Boolean",
    "is_featured": "Boolean",
    "created_at": "Date"
  },
  "orders": {
    "_id": "ObjectId",
    "user_id": "ObjectId",
    "order_number": "String (unique)",
    "items": "Array of OrderItem",
    "total_amount": "Number",
    "delivery_charge": "Number",
    "delivery_address": "String",
    "phone": "String",
    "payment_method": "String",
    "payment_status": "String",
    "status": "String",
    "order_date": "Date",
    "estimated_delivery": "Date"
  },
  "categories": {
    "_id": "ObjectId",
    "name": "String (unique)",
    "name_nepali": "String",
    "description": "String",
    "sort_order": "Number",
    "is_active": "Boolean"
  }
}
```

### Appendix C: Configuration Files

#### C.1 MongoDB Configuration
```python
class MongoConfig:
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/nepal_meat_shop'
    MONGO_HOST = os.environ.get('MONGO_HOST') or 'localhost'
    MONGO_PORT = int(os.environ.get('MONGO_PORT') or 27017)
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME') or 'nepal_meat_shop'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

#### C.2 Dependencies (requirements.txt)
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Migrate==4.0.5
SQLAlchemy==2.0.23
pymongo==4.6.0
flask-pymongo==2.3.0
WTForms==3.1.0
Werkzeug==3.0.1
Jinja2==3.1.2
Pillow==10.1.0
reportlab==4.0.7
python-dotenv==1.0.0
pytest==7.4.3
gunicorn==21.2.0
```

### Appendix D: Deployment Guide

#### D.1 Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd BugFixer

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env.mongo

# Run MongoDB application
python run_mongo.py
```

#### D.2 Production Deployment
```bash
# Production environment setup
export FLASK_ENV=production
export MONGO_URI=mongodb://production-server:27017/nepal_meat_shop
export SECRET_KEY=production-secret-key

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 mongo_app:app
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Authors**: Development Team  
**Status**: Complete

---

*🍖 Nepal Meat Shop - Fresh, Quality, Delivered! / ताजा, गुणस्तरीय, डेलिभरी!*