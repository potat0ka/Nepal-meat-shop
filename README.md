# 🍖 Nepal Meat Shop - E-commerce Platform

**A modern, bilingual e-commerce platform for meat products with MongoDB backend**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

**Last Updated**: January 2025 | **Status**: ✅ Cleaned & Optimized

---

## 🆕 Recent Platform Cleanup (January 2025)

✅ **Duplicate Files Removed**: Eliminated duplicate QR codes, profile templates, contact/about pages  
✅ **Cache Cleaned**: Removed all __pycache__ directories and compiled Python files  
✅ **Structure Organized**: Streamlined templates and static file organization  
✅ **Dependencies Updated**: Updated requirements.txt with correct Python 3.9+ dependencies  
✅ **Documentation Updated**: Fresh deployment guide and updated README  
✅ **Import References Verified**: All imports validated and working correctly  
✅ **Production Ready**: Cleaned codebase optimized for deployment  

A modern, clean Flask e-commerce application for a Nepali meat shop with MongoDB database and bilingual support (English/Nepali).

## 🏗️ Clean Architecture (Updated January 2025)

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
│   ├── enhanced_chat_v2.py # Enhanced chat system models
│   ├── chat.py             # Basic chat functionality models
│   ├── chat_learning.py    # AI learning and training models
│   └── analytics.py        # Analytics and reporting models
├── routes/                  # Route blueprints (MongoDB only)
│   ├── mongo_main.py       # Home and general routes
│   ├── mongo_auth.py       # Authentication routes
│   ├── mongo_products.py   # Product listing and details
│   ├── mongo_orders.py     # Cart and order management
│   ├── mongo_admin.py      # Admin panel routes
│   ├── chat.py             # Basic chat routes
│   ├── admin_chat.py       # Admin chat management
│   ├── enhanced_admin_chat.py # Enhanced admin chat features
│   ├── enhanced_chat_routes.py # Enhanced chat API routes
│   └── payment_*.py        # Payment gateway integration
├── forms/                   # WTForms definitions
│   ├── auth.py             # Authentication forms
│   ├── product.py          # Product-related forms
│   ├── order.py            # Order and cart forms
│   └── qr_code.py          # QR code forms
├── services/                # Business services
│   ├── enhanced_websocket_service.py # Enhanced WebSocket chat service
│   ├── chat_takeover_service.py # Admin takeover functionality
│   ├── enhanced_ai_service.py # AI chat assistant service
│   ├── ai_service_manager.py # AI service management
│   ├── gateways/           # Payment gateway implementations
│   └── payment_service.py  # Payment processing logic
└── utils/                   # Utility functions
    ├── mongo_db.py         # MongoDB connection and utilities
    ├── file_utils.py       # File upload and management
    ├── business.py         # Business logic utilities
    ├── validation.py       # Input validation utilities
    ├── chat_utils.py       # Chat utility functions
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

### 🤖 Enhanced AI Chat System
- **Smart Assistant**: Google Gemini-powered customer support with learning capabilities
- **Bilingual Chat**: Supports both English and Nepali conversations
- **Admin Takeover**: Silent human agent takeover with queue management
- **Role-Based Access**: Different chat features for customers, staff, and admins
- **Real-time Communication**: Enhanced WebSocket service with room management
- **Internal Messaging**: Admin-to-admin communication channels
- **Conversation History**: Persistent chat history with analytics and AI learning
- **Queue Management**: Automated conversation routing and priority handling

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
- **Responsive Design**: Mobile-first approach with Bootstrap framework
- **Clean Interface**: Modern, intuitive user interface design
- **Enhanced Chat Widget**: Streamlined chat interface with role-based features
- **Optimized Assets**: Consolidated JavaScript and CSS files for better performance

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (recommended: 3.11+)
- **MongoDB 4.4+** (recommended: 5.0+)
- **Google Gemini API Key** (for AI chat features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Nepal-meat-shop
   ```

2. **Run deployment script**
   
   **Windows (Command Prompt):**
   ```cmd
   scripts\deploy.bat
   ```
   
   **Windows (PowerShell):**
   ```powershell
   scripts\deploy.ps1
   ```
   
   **Linux/macOS:**
   ```bash
   chmod +x scripts/deploy.sh
   scripts/deploy.sh
   ```

3. **Configure environment**
   - Copy `.env.mongo` and update MongoDB connection settings
   - Set up payment gateway credentials (optional)
   - Configure Google Gemini API key for chat functionality (optional)

4. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Default admin credentials will be displayed in the terminal

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017/nepal_meat_shop

# Security
SECRET_KEY=your-secret-key-here

# AI Chat
GEMINI_API_KEY=your-gemini-api-key

# Payment Gateways
KHALTI_SECRET_KEY=your-khalti-secret
ESEWA_SECRET_KEY=your-esewa-secret
```

## 📁 Organized Project Structure (Updated January 2025)

```
Nepal-meat-shop/
├── app/                    # Application modules
│   ├── config/            # Configuration files
│   ├── forms/             # WTForms form definitions
│   ├── models/            # MongoDB models
│   ├── routes/            # Flask route handlers
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── scripts/               # Utility and deployment scripts
│   ├── check_session.py   # Session checking utility
│   ├── create_admin.py    # Admin user creation
│   ├── list_users.py      # User listing utility
│   ├── deploy.bat         # Windows deployment
│   ├── deploy.ps1         # PowerShell deployment
│   ├── deploy.sh          # Linux/macOS deployment
│   └── README.md          # Scripts documentation
├── static/                # Static assets (CSS, JS, images)
├── templates/             # Jinja2 HTML templates
├── uploads/               # User uploaded files
├── requirements.txt       # Python dependencies
├── mongo_app.py          # Main application entry point
├── documentation.md       # Technical documentation
├── deployment.md         # Deployment guide
└── .env.mongo            # Environment configuration
```

## 📖 Usage

### For Customers
- Browse products by category or search
- Add items to cart and proceed to checkout
- Choose from multiple payment options
- Track order status and history
- Use AI chat for instant support

### For Administrators
- Access admin panel at `/admin`
- Manage products, categories, and inventory
- Process orders and update delivery status
- Monitor business analytics and performance
- Configure payment gateways and QR codes
- Manage customer support conversations

## 🛠️ Technology Stack

- **Backend**: Python 3.9+, Flask 3.0.3
- **Database**: MongoDB 4.4+ with PyMongo 4.8.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **AI Integration**: Google Gemini API
- **Payment**: eSewa, Khalti, IME Pay, FonePay
- **Real-time**: WebSocket for chat functionality
- **Security**: CSRF protection, input validation, secure sessions

## 🔧 Configuration

### Environment Variables (.env.mongo)
```env
MONGO_URI=mongodb://localhost:27017/nepal_meat_shop
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
ESEWA_MERCHANT_ID=your-esewa-merchant-id
KHALTI_SECRET_KEY=your-khalti-secret-key
```

### MongoDB Setup
- Install MongoDB Community Edition 5.0+
- Start MongoDB service
- Database and collections are created automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed setup
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Chat**: Use the built-in AI chat system for quick questions

---

**Made with ❤️ for the Nepal Meat Shop community**