# 🍖 Nepal Meat Shop - Deployment Instructions

**Last Updated**: January 2025  
**Platform Status**: ✅ Production Ready (Cleaned & Optimized)

Step-by-step instructions to run and deploy the Nepal Meat Shop Python + MongoDB platform.

## Platform Overview
- ✅ **Clean Codebase**: Removed duplicate files, unused code, and __pycache__ directories
- ✅ **MongoDB Integration**: Fully functional with enhanced chat system
- ✅ **Payment Gateways**: eSewa, Khalti, and other Nepali payment methods
- ✅ **Enhanced AI Chat**: Google Gemini-powered with role-based access and WebSocket
- ✅ **Admin Panel**: Complete business management interface
- ✅ **Updated Dependencies**: Latest versions in requirements.txt
- ✅ **Organized Structure**: Streamlined templates and static files

## Prerequisites

### System Requirements
- **Python**: 3.9+ (recommended: 3.11+)
- **MongoDB**: 4.4+ (recommended: 5.0+)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 2GB RAM
- **Storage**: 1GB free space

### Required Software
1. **Python 3.9+**: [Download from python.org](https://python.org)
2. **MongoDB**: [Download Community Edition](https://mongodb.com/try/download/community)
3. **Git**: [Download from git-scm.com](https://git-scm.com)

## Quick Deployment

### Option 1: Automated Scripts (Recommended)

#### Windows
```bash
# Run the deployment script
deploy.bat

# Or use PowerShell
.\deploy.ps1
```

#### macOS/Linux
```bash
# Make executable and run
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd Nepal-meat-shop
```

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Required variables:
# MONGODB_URI=mongodb://localhost:27017/nepal_meat_shop
# SECRET_KEY=your-secret-key-here
# GEMINI_API_KEY=your-gemini-api-key
```

#### Step 5: Setup MongoDB
```bash
# Start MongoDB service
# Windows: Start MongoDB service from Services
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# Create admin user (optional)
python create_admin.py
```

#### Step 6: Run Application
```bash
# Development mode
python mongo_app.py

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 mongo_app:app
```

## Configuration

### Environment Variables (.env)
```bash
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/nepal_meat_shop
MONGODB_DB_NAME=nepal_meat_shop

# Application Security
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production

# AI Chat Configuration
GEMINI_API_KEY=your-gemini-api-key
CHAT_MODEL=gpt-3.5-turbo

# Payment Gateway Configuration
KHALTI_SECRET_KEY=your-khalti-secret
ESEWA_SECRET_KEY=your-esewa-secret

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### MongoDB Configuration
```bash
# Local MongoDB (default)
MONGODB_URI=mongodb://localhost:27017/nepal_meat_shop

# MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/nepal_meat_shop

# MongoDB with authentication
MONGODB_URI=mongodb://username:password@localhost:27017/nepal_meat_shop
```

## Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install Gunicorn (already in requirements.txt)
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 mongo_app:app

# With configuration file
gunicorn -c gunicorn.conf.py mongo_app:app
```

### Using Docker (Optional)
```dockerfile
# Dockerfile example
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "mongo_app:app"]
```

### Nginx Configuration (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /path/to/Nepal-meat-shop/static;
    }
}
```

## Verification

### Check Application Status
1. **Web Interface**: Visit `http://localhost:5000`
2. **Admin Panel**: Visit `http://localhost:5000/admin`
3. **API Health**: Visit `http://localhost:5000/api/health`
4. **Chat System**: Test the chat widget on the homepage

### Test Core Features
- ✅ User registration and login
- ✅ Product browsing and search
- ✅ Shopping cart functionality
- ✅ Order placement and tracking
- ✅ Payment gateway integration
- ✅ AI chat assistant
- ✅ Admin panel access

## Troubleshooting

### Common Issues

#### MongoDB Connection Error
```bash
# Check MongoDB status
# Windows: Check Services
# macOS: brew services list | grep mongodb
# Linux: sudo systemctl status mongod

# Restart MongoDB
# Windows: Restart MongoDB service
# macOS: brew services restart mongodb-community
# Linux: sudo systemctl restart mongod
```

#### Port Already in Use
```bash
# Find process using port 5000
# Windows: netstat -ano | findstr :5000
# macOS/Linux: lsof -i :5000

# Kill process or use different port
export PORT=8000
python mongo_app.py
```

#### Gemini API Error
```bash
# Check API key in .env file
# Verify Gemini API access
# Test API key: https://aistudio.google.com/app/apikey
```

### Log Files
- **Application Logs**: Check console output
- **MongoDB Logs**: Check MongoDB log directory
- **Error Logs**: Check Flask debug output

## Maintenance

### Regular Tasks
1. **Update Dependencies**: `pip install -r requirements.txt --upgrade`
2. **Backup Database**: Use MongoDB backup tools
3. **Monitor Logs**: Check for errors and performance issues
4. **Update Environment**: Keep Python and MongoDB updated

### Security Updates
1. **Change Secret Keys**: Regularly update SECRET_KEY
2. **Update Dependencies**: Keep packages updated
3. **Monitor Access**: Check admin panel access logs
4. **SSL Certificate**: Use HTTPS in production

## Support

For issues or questions:
1. Check this deployment guide
2. Review application logs
3. Check MongoDB connection
4. Verify environment variables
5. Test with fresh virtual environment

---

**Note**: This platform has been cleaned and optimized. All duplicate files, debug code, and unnecessary utilities have been removed for production readiness.