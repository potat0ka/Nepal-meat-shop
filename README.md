# 🍖 Nepal Meat Shop - MongoDB Version

A modern, modular Flask e-commerce application for a Nepali meat shop with MongoDB database and bilingual support (English/Nepali).

## 🏗️ Architecture

The application has been completely refactored into a modular, maintainable structure:

```
app/
├── __init__.py              # Application factory
├── config/                  # Configuration management
│   ├── __init__.py
│   └── settings.py         # Environment-specific settings
├── models/                  # Database models
│   ├── __init__.py
│   ├── user.py             # User and authentication models
│   ├── product.py          # Product and category models
│   ├── order.py            # Order and cart models
│   └── analytics.py        # Analytics and reporting models
├── routes/                  # Route blueprints
│   ├── __init__.py
│   ├── main.py             # Home and general routes
│   ├── auth.py             # Authentication routes
│   ├── products.py         # Product listing and details
│   └── orders.py           # Cart and order management
├── forms/                   # WTForms definitions
│   ├── __init__.py
│   ├── auth.py             # Authentication forms
│   ├── product.py          # Product-related forms
│   └── order.py            # Order and cart forms
└── utils/                   # Utility functions
    ├── __init__.py
    ├── file_utils.py       # File upload and management
    ├── business.py         # Business logic utilities
    └── validation.py       # Input validation utilities
```

## ✨ Features

### 🛒 E-commerce Functionality
- Product catalog with categories and filtering
- Shopping cart with session management
- Multi-step checkout process
- Order tracking and history
- Product reviews and ratings

### 🔐 User Management
- User registration and authentication
- Profile management
- Password change functionality
- Session-based cart persistence

### 💰 Payment Integration
- Cash on Delivery (COD)
- Digital payment simulation (eSewa, Khalti, PhonePay)
- Mobile banking and bank transfer options

### 🌐 Bilingual Support
- English and Nepali language support
- Localized product names and descriptions
- Bilingual user interface

### 📱 Modern UI/UX
- Responsive Bootstrap design
- Mobile-friendly interface
- Clean, modern aesthetics
- Intuitive navigation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- MongoDB (local installation or MongoDB Atlas account)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BugFixer
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
   
   See `MONGODB_SETUP.md` for detailed MongoDB installation instructions.

4. **Run the MongoDB application**
   ```bash
   python run_mongo.py
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

### Models
- **User**: Customer accounts and authentication
- **Product**: Meat products with categories and stock
- **Order**: Order processing and tracking
- **Analytics**: Sales reporting and notifications

### Routes (Blueprints)
- **Main**: Homepage, search, and general pages
- **Auth**: Login, registration, and profile management
- **Products**: Product listing, details, and reviews
- **Orders**: Shopping cart and order processing

### Utilities
- **File Utils**: Image upload and file management
- **Business**: Order processing and pricing logic
- **Validation**: Input validation and sanitization

## 🛠️ Development

### Running in Development Mode
```bash
# Set environment
export FLASK_ENV=development

# Run with auto-reload
python run_mongo.py
```

### Database Migrations
```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

### Adding New Features

1. **Models**: Add to appropriate model file in `app/models/`
2. **Routes**: Create new blueprint or add to existing in `app/routes/`
3. **Forms**: Add form classes to `app/forms/`
4. **Templates**: Add HTML templates to `templates/`
5. **Utilities**: Add helper functions to `app/utils/`

## 🔒 Security Features

- CSRF protection on all forms
- Secure password hashing
- Input validation and sanitization
- File upload security
- Session management

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