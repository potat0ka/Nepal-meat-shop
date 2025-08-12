# 🍖 Nepal Meat Shop - Complete Deployment Guide

This comprehensive guide covers all deployment methods for the Nepal Meat Shop application across Windows, macOS, and Linux platforms.

## 🆕 Recent Updates (December 2024)
- ✅ **MongoDB Atlas Migration**: Application now uses cloud database exclusively
- ✅ **Simplified Entry Point**: All platforms now use `mongo_app.py` as the main application file
- ✅ **Cleaned Codebase**: Removed dummy files, test scripts, and cache files
- ✅ **Updated Scripts**: All deployment scripts updated to reflect current architecture

## 🚀 Quick Start (One-Click Deployment)

### Automated Deployment Scripts

The easiest way to deploy the application is using our automated scripts:

#### Windows Users
```bash
# Option 1: Batch Script (Recommended)
deploy.bat

# Option 2: PowerShell Script (Advanced)
.\deploy.ps1
.\deploy.ps1 -Verbose    # With detailed output
.\deploy.ps1 -Force      # Force reinstall dependencies
```

#### macOS/Linux Users
```bash
# Make executable and run
chmod +x deploy.sh && ./deploy.sh
```

### What the Automated Scripts Do
- ✅ Check Python installation (3.6+ required)
- ✅ Create virtual environment automatically
- ✅ Install/update dependencies intelligently
- ✅ Load environment variables from `.env.mongo`
- ✅ Start the application on `http://127.0.0.1:5000`

---

## 📋 Manual Deployment by Platform

### 🍎 macOS Setup

#### Prerequisites
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.7+
brew install python
```

#### MongoDB Installation
```bash
# Option 1: Local MongoDB (Recommended for Development)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Option 2: Use MongoDB Atlas (Cloud) - see Atlas section below
```

#### Application Setup
```bash
# Navigate to project directory
cd /path/to/nepal-meat-shop

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables (optional)
export FLASK_ENV=development
export MONGO_URI=mongodb://localhost:27017/nepal_meat_shop_dev

# Run the application
python3 mongo_app.py
```

### 🐧 Linux Setup

#### Prerequisites by Distribution
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

#### MongoDB Installation

**Ubuntu/Debian:**
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**CentOS/RHEL/Fedora:**
```bash
# Create MongoDB repository file
sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo << EOF
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

# Install and start MongoDB
sudo yum install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Application Setup
```bash
# Install dependencies and run
pip3 install -r requirements.txt
python3 mongo_app.py
```

### 🪟 Windows Setup

#### Prerequisites
1. Download Python from [python.org](https://www.python.org/downloads/)
2. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
3. Verify: `python --version`

#### MongoDB Installation
- **Option 1**: Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
- **Option 2**: Use MongoDB Atlas (Cloud) - see Atlas section below

#### Application Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Run the application
python mongo_app.py
```

---

## ☁️ MongoDB Atlas (Cloud) Setup

### For All Platforms

1. **Create Account**: Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

2. **Create Cluster**:
   - Choose "Build a Database"
   - Select "Free" tier (M0 Sandbox)
   - Choose a region close to you

3. **Database Access**:
   - Go to "Database Access"
   - Add new database user
   - Choose "Password" authentication
   - Save username and password

4. **Network Access**:
   - Go to "Network Access"
   - Add IP address: `0.0.0.0/0` (for development)

5. **Get Connection String**:
   - Go to "Clusters" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string

6. **Set Environment Variable**:
   ```bash
   # Create .env.mongo file
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/nepal_meat_shop?retryWrites=true&w=majority
   ```

---

## 🔧 Environment Configuration

### .env.mongo File
Create this file in your project root:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/nepal_meat_shop_dev
MONGO_DB_NAME=nepal_meat_shop_dev

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Payment Configuration (for testing)
PAYMENT_ENVIRONMENT=sandbox
KHALTI_ENABLED=true
ESEWA_ENABLED=true

# eSewa Configuration
ESEWA_MERCHANT_ID=your_merchant_id
ESEWA_SECRET_KEY=your_secret_key

# Khalti Configuration
KHALTI_PUBLIC_KEY=your_public_key
KHALTI_SECRET_KEY=your_secret_key
```

---

## 🔍 Troubleshooting

### Common Issues

#### "Python is not installed or not in PATH"
**Solutions:**
- **Windows**: Reinstall Python with "Add to PATH" checked
- **macOS**: `brew install python3`
- **Linux**: Use package manager (see platform-specific instructions above)

#### "Failed to create virtual environment"
```bash
# Test Python venv module
python -m venv test_env

# If fails, install venv
# Ubuntu/Debian
sudo apt install python3-venv
```

#### "Failed to install dependencies"
**Solutions:**
1. Check internet connection
2. Update pip: `python -m pip install --upgrade pip`
3. Clear pip cache: `pip cache purge`
4. Try with `--no-cache-dir`: `pip install --no-cache-dir -r requirements.txt`

#### MongoDB Connection Issues
```bash
# Check MongoDB status
# macOS (Homebrew)
brew services list | grep mongodb

# Linux
sudo systemctl status mongod

# Windows
net start MongoDB
```

#### PowerShell Execution Policy Error
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Platform-Specific Troubleshooting

#### macOS Issues
```bash
# MongoDB not found
brew tap mongodb/brew
brew install mongodb-community

# Permission issues
sudo chown -R $(whoami) ~/data/db

# Port conflicts
lsof -i :27017
```

#### Linux Issues
```bash
# MongoDB service issues
sudo systemctl status mongod
sudo journalctl -u mongod
sudo systemctl restart mongod

# Permission issues
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown mongodb:mongodb /tmp/mongodb-27017.sock

# Firewall issues
sudo ufw allow 27017
```

#### Windows Issues
```powershell
# Check MongoDB service
Get-Service MongoDB

# Start MongoDB service
net start MongoDB

# Check port usage
netstat -an | findstr :27017
```

---

## 📊 Advanced Features

### Smart Dependency Management
- ✅ Detects when `requirements.txt` changes
- ✅ Only reinstalls when necessary
- ✅ Caches installation state using MD5 hashes
- ✅ Upgrades pip automatically

### Cross-Platform Compatibility
- ✅ **Windows**: Batch (.bat) and PowerShell (.ps1) scripts
- ✅ **macOS**: Shell script with Homebrew integration
- ✅ **Linux**: Multi-distribution support (Ubuntu, CentOS, Fedora, Arch)

### Environment Management
- ✅ Automatic virtual environment creation
- ✅ Environment variable loading from `.env.mongo`
- ✅ Development mode configuration
- ✅ Python path management

---

## 🚀 Production Deployment

### Docker Deployment (All Platforms)

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "mongo_app.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MONGO_URI=mongodb://mongo:27017/nepal_meat_shop
    depends_on:
      - mongo
  
  mongo:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

### Systemd Service (Linux)
```ini
# /etc/systemd/system/nepal-meat-shop.service
[Unit]
Description=Nepal Meat Shop Application
After=network.target mongod.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/nepal-meat-shop
Environment=MONGO_URI=mongodb://localhost:27017/nepal_meat_shop
ExecStart=/usr/bin/python3 mongo_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔄 Development Workflow

### Making Changes
1. Edit your code
2. Update `requirements.txt` if needed
3. Run deployment script
4. Script automatically detects changes and updates dependencies

### Testing Different Environments
```bash
# Force reinstall dependencies
.\deploy.ps1 -Force          # Windows PowerShell
rm -rf venv/ && ./deploy.sh  # macOS/Linux

# Clean start
rm -rf venv/        # macOS/Linux
rmdir /s venv       # Windows
```

---

## 🌐 Application Access

Once deployed successfully:
- **Local URL**: http://127.0.0.1:5000
- **Network URL**: http://localhost:5000
- **Admin Panel**: http://127.0.0.1:5000/admin
- **API Endpoints**: http://127.0.0.1:5000/api/

### Default Admin Access
- **Username**: admin
- **Password**: Check the application logs or create using `add_staff_user.py`

---

## 📊 Performance Optimization

### MongoDB Optimization
```javascript
// Create indexes for better performance
db.products.createIndex({ "name": "text", "description": "text" })
db.orders.createIndex({ "user_id": 1, "created_at": -1 })
db.users.createIndex({ "email": 1 }, { unique: true })
```

### Application Optimization
```python
# Use connection pooling
MONGO_URI = "mongodb://localhost:27017/nepal_meat_shop?maxPoolSize=50"

# Enable compression
MONGO_URI = "mongodb://localhost:27017/nepal_meat_shop?compressors=zlib"
```

---

## 🔍 Monitoring and Logging

### Application Logs
```bash
# View application logs
tail -f /var/log/nepal-meat-shop/app.log

# MongoDB logs
# macOS (Homebrew)
tail -f /usr/local/var/log/mongodb/mongo.log

# Linux
tail -f /var/log/mongodb/mongod.log
```

### Health Checks
```bash
# Check application health
curl http://localhost:5000/

# Check MongoDB health
mongo --eval "db.adminCommand('ping')"
```

---

## 🛑 Stopping the Application

- Press `Ctrl+C` in the terminal
- The script will handle graceful shutdown
- Virtual environment remains active for next run

---

## 🔒 Security Notes

- Scripts load environment variables from `.env.mongo`
- Never commit sensitive data to version control
- Use strong secret keys in production
- Consider using environment-specific configuration files
- For production, use proper SSL/TLS certificates

---

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Verify Python and pip installation
3. Ensure all prerequisites are met
4. Check console output for specific error messages
5. Review MongoDB connection and status

### Common Support Resources
- **MongoDB Documentation**: [docs.mongodb.com](https://docs.mongodb.com)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **Python Virtual Environments**: [docs.python.org/3/tutorial/venv.html](https://docs.python.org/3/tutorial/venv.html)

---

**Happy Deploying! 🚀**

*This guide covers all deployment scenarios from development to production. Choose the method that best fits your needs and environment.*