# 🍖 Nepal Meat Shop - MongoDB Setup Guide

This guide will help you set up MongoDB for the Nepal Meat Shop application.

## Option 1: Local MongoDB Installation (Recommended for Development)

### Windows Installation:

1. **Download MongoDB Community Server:**
   - Visit: https://www.mongodb.com/try/download/community
   - Select Windows platform
   - Download the MSI installer

2. **Install MongoDB:**
   - Run the downloaded MSI file
   - Choose "Complete" installation
   - Install MongoDB as a Service (recommended)
   - Install MongoDB Compass (GUI tool)

3. **Verify Installation:**
   ```powershell
   # Check if MongoDB service is running
   Get-Service -Name MongoDB
   
   # Or start MongoDB manually
   mongod --dbpath "C:\data\db"
   ```

4. **Create Data Directory (if needed):**
   ```powershell
   mkdir C:\data\db
   ```

### Linux/macOS Installation:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y mongodb

# macOS with Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # macOS
```

## Option 2: MongoDB Atlas (Cloud Database)

1. **Create Free Account:**
   - Visit: https://www.mongodb.com/cloud/atlas
   - Sign up for a free account

2. **Create Cluster:**
   - Create a new cluster (free tier available)
   - Choose a region close to you
   - Wait for cluster to be created

3. **Setup Database Access:**
   - Go to Database Access
   - Add a new database user
   - Note down username and password

4. **Setup Network Access:**
   - Go to Network Access
   - Add IP address (0.0.0.0/0 for development)

5. **Get Connection String:**
   - Go to Clusters → Connect
   - Choose "Connect your application"
   - Copy the connection string

6. **Update Environment Variables:**
   ```bash
   # Create .env file with your Atlas connection
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/nepal_meat_shop?retryWrites=true&w=majority
   ```

## Running the Application

### 1. Install Dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Set Environment Variables:
```powershell
# For local MongoDB
$env:MONGO_URI="mongodb://localhost:27017/nepal_meat_shop"

# For MongoDB Atlas
$env:MONGO_URI="your_atlas_connection_string_here"
```

### 3. Run the Application:
```powershell
python run_mongo.py
```

## User Management

The application uses only real MongoDB data. Admin users can:
- Create new user accounts through the admin panel
- Manage products and categories
- Process orders and manage inventory

To create your first admin user, you can use the admin registration feature or create one directly in MongoDB.

## Troubleshooting

### MongoDB Connection Issues:

1. **Check if MongoDB is running:**
   ```powershell
   # Windows
   Get-Service -Name MongoDB
   
   # Or check process
   Get-Process -Name mongod
   ```

2. **Start MongoDB manually:**
   ```powershell
   # Windows
   net start MongoDB
   
   # Or start manually
   mongod --dbpath "C:\data\db"
   ```

3. **Check MongoDB logs:**
   - Windows: `C:\Program Files\MongoDB\Server\7.0\log\mongod.log`
   - Linux: `/var/log/mongodb/mongod.log`

### Application Issues:

1. **Import Errors:**
   ```powershell
   pip install pymongo flask-pymongo
   ```

2. **Permission Issues:**
   - Make sure the data directory has proper permissions
   - Run as administrator if needed

3. **Port Conflicts:**
   - Default MongoDB port is 27017
   - Check if another service is using this port

## MongoDB Compass (GUI Tool)

If you installed MongoDB Compass:
1. Open MongoDB Compass
2. Connect to `mongodb://localhost:27017`
3. Browse your `nepal_meat_shop` database
4. View collections: users, products, categories, orders

## Production Considerations

For production deployment:
1. Use MongoDB Atlas or a managed MongoDB service
2. Set up proper authentication and authorization
3. Configure SSL/TLS encryption
4. Set up regular backups
5. Monitor performance and logs
6. Use environment variables for sensitive data

## Need Help?

- MongoDB Documentation: https://docs.mongodb.com/
- MongoDB University: https://university.mongodb.com/
- Community Forums: https://community.mongodb.com/