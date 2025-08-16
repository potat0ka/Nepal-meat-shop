# 🍖 Nepal Meat Shop - E-commerce Platform

**A modern, bilingual e-commerce platform for meat products with MongoDB backend**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0+-green.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

**Last Updated**: January 2025 | **Status**: ✅ Cleaned & Optimized

---

A modern, clean Flask e-commerce application for a Nepali meat shop with MongoDB database and bilingual support (English/Nepali).

## 🏗️ Clean Architecture (Updated December 2024)

The application has been cleaned up and organized with a streamlined structure:

```
app/
├── __init__.py              # Application factory
├── config/                  # Configuration management
│   ├── mongo_settings.py   # MongoDB configuration
│   ├── payment_config.py   # Payment gateway settings
│   └── settings.py         # General app settings
├── models/                  # Database models (MongoDB only)
│   ├── mongo_models.py     # MongoDB user, product, order models
│   ├── chat.py             # Chat functionality models
│   └── analytics.py        # Analytics and reporting models
├── routes/                  # Route blueprints (MongoDB only)
│   ├── mongo_main.py       # Home and general routes
│   ├── mongo_auth.py       # Authentication routes
│   ├── mongo_products.py   # Product listing and details
│   ├── mongo_orders.py     # Cart and order management
│   ├── mongo_admin.py      # Admin panel routes
│   ├── chat.py             # AI chat assistant
│   └── payment_*.py        # Payment gateway integration
├── forms/                   # WTForms definitions
│   ├── auth.py             # Authentication forms
│   ├── product.py          # Product-related forms
│   ├── order.py            # Order and cart forms
│   └── qr_code.py          # QR code forms
├── services/                # Business services
│   ├── gateways/           # Payment gateway implementations
│   └── payment_service.py  # Payment processing logic
└── utils/                   # Utility functions
    ├── mongo_db.py         # MongoDB connection and utilities
    ├── file_utils.py       # File upload and management
    ├── business.py         # Business logic utilities
    ├── validation.py       # Input validation utilities
    └── analytics.py        # Analytics utilities
```

## ✨ Key Features

### 🛒 E-commerce Core
- **Product Management**: Complete CRUD operations with optimized image handling
- **Shopping Cart**: Session-based cart with real-time quantity management
- **Order Processing**: Full order lifecycle from cart to delivery tracking
- **Payment Integration**: Multiple Nepali payment gateways (eSewa, Khalti, IME Pay)
- **Invoice Generation**: Automated PDF invoice creation with business branding

### 🌐 Bilingual Support
- **Dual Language**: Full English and Nepali language support
- **Dynamic Content**: Language-aware product descriptions and UI
- **Cultural Adaptation**: Nepali currency, address formats, and business practices
- **Smart Detection**: Automatic language detection for user inputs

### 🤖 AI-Powered Chat System
- **Smart Assistant**: OpenAI GPT-powered customer support
- **Bilingual Chat**: Supports both English and Nepali conversations
- **Admin Takeover**: Human agents can seamlessly take over conversations
- **Real-time Communication**: WebSocket-based instant messaging
- **Conversation History**: Persistent chat history and analytics

### 👨‍💼 Admin Panel
- **Business Dashboard**: Real-time analytics and key performance metrics
- **User Management**: Customer and staff account administration
- **Order Management**: Process orders, update delivery status, track performance
- **Product Management**: Add, edit, and manage product catalog with categories
- **Payment Configuration**: Manage payment gateway settings and QR codes
- **Chat Management**: Monitor and manage customer conversations

### 🔐 Security & Authentication
- **User Authentication**: Secure registration and login with password hashing
- **Role-Based Access**: Hierarchical permissions (Admin, Sub-Admin, Staff, Customer)
- **Session Security**: Secure session handling with CSRF protection
- **Input Validation**: Comprehensive server-side validation and sanitization

### 🗺️ Location Services
- **Interactive Maps**: Leaflet.js integration with click-to-select functionality
- **Current Location**: HTML5 Geolocation API with comprehensive error handling
- **Address Search**: Nominatim API integration for location search
- **Delivery Zones**: Coordinate-based delivery location management

### 📱 Modern UI/UX
- **Responsive Design**: Mobile-first Bootstrap framework implementation
- **Progressive Enhancement**: Graceful degradation across devices
- **Interactive Elements**: Dynamic content loading and real-time updates
- **Accessibility**: User-friendly interface with intuitive navigation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- MongoDB Atlas account (cloud database - recommended)

### Recent Updates (December 2024)
- ✅ **Migrated to MongoDB Atlas**: Application now uses cloud database instead of local SQLite
- ✅ **Cleaned up dummy files**: Removed development database files and test scripts
- ✅ **Streamlined deployment**: Updated all deployment scripts to use `mongo_app.py`
- ✅ **Removed cache files**: Cleaned up Python cache files for better performance

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nepal-meat-shop
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB and environment variables**
   ```bash
   # Create .env.mongo file
   MONGO_URI=mongodb://localhost:27017/nepal_meat_shop
   # Or for MongoDB Atlas:
   # MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/nepal_meat_shop
   
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   ```
   
   See `DEPLOYMENT_GUIDE.md` for detailed MongoDB installation and deployment instructions.

4. **Run the MongoDB application**
   ```bash
   python mongo_app.py
   ```

5. **Access the application**
   - Open your browser to `http://127.0.0.1:5000`

## 🔧 Configuration

The application supports multiple environments:

- **Development**: Default configuration with debug mode
- **Production**: Optimized for production deployment
- **Testing**: Configuration for running tests

Environment can be set via `FLASK_ENV` environment variable.

## 📁 Project Structure

### Core Application
```
BugFixer/
├── mongo_app.py           # MongoDB application entry point
├── requirements.txt       # Python dependencies
├── .env.mongo            # Environment configuration
└── documentation.md      # Technical documentation
```

### Templates & Frontend
```
templates/
├── base.html             # Base template with navigation
├── admin/               # Administrative interface
│   ├── dashboard.html   # Admin dashboard with statistics
│   ├── users.html       # User management interface
│   ├── products.html    # Product management
│   ├── orders.html      # Order processing
│   ├── categories.html  # Category management
│   ├── payment_gateways.html  # Payment configuration
│   └── business_insights.html # Analytics dashboard
├── orders/              # Order management templates
│   ├── checkout.html    # Enhanced checkout with maps
│   ├── cart.html        # Shopping cart interface
│   ├── order_detail.html # Order tracking
│   └── invoice.html     # Order invoices
├── pages/               # Static and informational pages
└── errors/              # Error handling templates
```

### Key Features Implementation
- **MongoDB Integration**: Document-based data storage with flexible schema
- **Blueprint Architecture**: Modular route organization for maintainability
- **Location Services**: Leaflet.js maps with geolocation and address search
- **Payment Systems**: Multi-gateway support with QR code integration
- **Admin Panel**: Comprehensive management interface with analytics
- **Security**: Role-based access control with CSRF protection
- **Bilingual Support**: English/Nepali localization throughout the application

## 🛠️ Development

### Technology Stack
- **Backend**: Flask 3.0.0 with MongoDB integration
- **Database**: MongoDB with PyMongo driver
- **Frontend**: Bootstrap 5, Leaflet.js for maps, vanilla JavaScript
- **Authentication**: Flask-Login with secure session management
- **Forms**: Flask-WTF with CSRF protection
- **File Handling**: Pillow for image processing
- **PDF Generation**: ReportLab for invoice generation

### Running in Development Mode
```bash
# Set environment variables
export FLASK_ENV=development
export MONGO_URI=mongodb://localhost:27017/nepal_meat_shop_dev

# Run with auto-reload
python mongo_app.py
```

### Database Setup
```bash
# MongoDB setup (local installation)
# Install MongoDB Community Edition
# Start MongoDB service
mongod --dbpath /path/to/data/directory

# Or use MongoDB Atlas (cloud)
# Set MONGO_URI to your Atlas connection string
export MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/nepal_meat_shop
```

### Adding New Features

1. **Routes**: Add new routes to `mongo_main.py` or create new blueprint files
2. **Templates**: Add HTML templates to appropriate directories in `templates/`
3. **Static Assets**: Add CSS, JS, images to `static/` directory
4. **Database Models**: Define MongoDB document structures in route handlers
5. **Forms**: Create WTForms classes for user input validation

### Development Workflow
```bash
# 1. Make changes to code
# 2. Test locally with development server
python run_mongo.py

# 3. Check for errors in browser console and terminal
# 4. Test admin panel functionality at /admin
# 5. Test payment gateway integration
# 6. Verify location services on checkout page
```

## 🔒 Security Features

- **CSRF Protection**: All forms protected against cross-site request forgery
- **Password Security**: PBKDF2 hashing with salt for secure password storage
- **Input Validation**: Comprehensive server-side validation and sanitization
- **File Upload Security**: Restricted file types and size limits for uploads
- **Session Management**: Secure session handling with proper timeout
- **Role-Based Access**: Hierarchical permission system with granular controls
- **SQL Injection Prevention**: Parameterized queries and input sanitization

## 🚀 Recent Enhancements

### Location Services Integration
- **Interactive Maps**: Full Leaflet.js integration with responsive design
- **Geolocation API**: Current location detection with comprehensive error handling
- **Address Search**: Real-time address search using Nominatim API
- **Delivery Zones**: Precise coordinate-based delivery location management

### Enhanced Payment System
- **QR Code Integration**: Dynamic QR code generation for digital payments
- **Gateway Management**: Admin panel for payment gateway configuration
- **Multi-Method Support**: Support for 6+ payment methods including digital wallets
- **Payment Testing**: Built-in gateway testing and status monitoring

### Advanced Admin Features
- **Business Insights**: Comprehensive analytics dashboard with charts and metrics
- **Real-time Statistics**: Live order, user, and product statistics
- **User Role Management**: Advanced role-based access control system
- **Order Processing**: Streamlined order management with status tracking

## 📊 Key Improvements

### Code Organization
- ✅ Modular blueprint-based architecture
- ✅ Separation of concerns
- ✅ Reusable utility functions
- ✅ Centralized configuration management

### Performance
- ✅ Optimized database queries
- ✅ Efficient session management
- ✅ Proper error handling
- ✅ Logging and monitoring

### Maintainability
- ✅ Clear code structure
- ✅ Comprehensive documentation
- ✅ Type hints and docstrings
- ✅ Consistent naming conventions

### Security
- ✅ Input validation
- ✅ CSRF protection
- ✅ Secure file uploads
- ✅ Password security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support or questions, please create an issue in the repository.

---

**🍖 Nepal Meat Shop** - Fresh, Quality, Delivered! / ताजा, गुणस्तरीय, डेलिभरी!