# Overview

Nepal Meat Shop is a specialized eCommerce platform designed for delivering fresh pork and buffalo meat in Nepal's Kathmandu Valley. The application serves as a comprehensive meat delivery service with bilingual support (English/Nepali), featuring user authentication, product catalog management, shopping cart functionality, order processing, and administrative tools. The platform caters specifically to the Nepalese market with cultural considerations and local language support.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses server-side rendered HTML templates with Bootstrap 5 for responsive design and Font Awesome for icons. The frontend architecture follows a traditional MVC pattern with Flask handling routing and Jinja2 templating. JavaScript functionality is implemented in a modular approach with separate files for different features. The UI supports bilingual content display with Nepali and English text throughout the interface. Templates are organized by functionality (admin, auth, products, orders, etc.) with a base template providing common layout elements.

## Backend Architecture
Built on Flask framework with SQLAlchemy ORM for database operations. The application follows a modular structure separating concerns into distinct files:
- `app.py` - Application factory and configuration with database initialization
- `models.py` - Database models defining relationships between users, products, orders, and categories
- `routes.py` - URL routing and view logic handling all HTTP requests
- `forms.py` - WTForms for input validation and form rendering
- `utils.py` - Helper functions for file handling, order number generation, and utility operations

Authentication is handled via Flask-Login with role-based access control distinguishing between customers and administrators. The application uses the application factory pattern for better configuration management and testing capabilities.

## Data Storage
Uses SQLAlchemy with configurable database backends (defaults to SQLite for development, supports PostgreSQL for production via DATABASE_URL environment variable). The database schema includes comprehensive models for:
- User management with customer and admin roles
- Product catalog with categories, meat types, and detailed product information
- Shopping cart system with quantity management
- Order processing with status tracking and order items
- Review and rating system for products
- Delivery area management for service coverage
- Notification templates and logging system

Connection pooling and health checks are configured for production reliability with automatic reconnection handling.

## Authentication and Authorization
Implements Flask-Login for session management with secure password hashing via Werkzeug. The system supports:
- User registration with form validation
- Secure login with email and password
- Role-based access control (customer vs admin)
- Session management with configurable secret keys
- Protected routes requiring authentication
- Admin-only sections for product and order management
- Password reset functionality (template structure exists)

## File Management
Custom file upload system handles product images and other media files with:
- Unique filename generation using timestamps and UUIDs to prevent conflicts
- File type validation restricting uploads to image formats
- Organized storage in categorized upload directories
- Secure file serving through Flask routes with proper access control
- Image processing and optimization capabilities

# External Dependencies

## Core Framework Dependencies
- **Flask** (2.3.0+) - Web application framework providing routing, templating, and request handling
- **Flask-SQLAlchemy** (3.0.0+) - Database ORM integration for model definitions and query operations
- **Flask-Login** (0.6.0+) - User session management and authentication
- **Flask-WTF** (1.1.0+) - Form handling with CSRF protection and validation
- **WTForms** (3.0.0+) - Form field definitions and validation rules
- **Werkzeug** (2.3.0+) - WSGI utilities and security functions including password hashing

## Database Systems
- **SQLite** - Default development database (built-in Python support)
- **PostgreSQL** - Production database via psycopg2 driver (configurable via DATABASE_URL)

## File Processing and Utilities
- **Pillow** (9.0.0+) - Image processing library for product image handling and optimization
- **python-dotenv** (1.0.0+) - Environment variable management for configuration

## Deployment and Production
- **Gunicorn** (20.0.0+) - WSGI HTTP server for production deployment
- **ProxyFix middleware** - Handles reverse proxy headers for proper URL generation

## Frontend Resources (CDN-based)
- **Bootstrap 5** - CSS framework for responsive design and component styling
- **Font Awesome 6** - Icon library for UI elements and visual indicators
- **jQuery** (implied by JavaScript functionality) - DOM manipulation and AJAX requests

## Email and Notification Services
The application includes notification infrastructure with configurable SMTP settings for:
- Order confirmation emails
- Status update notifications
- User registration confirmations
- Admin alerts and reports

Support for SMS notifications is architected but requires external SMS service integration via API keys.