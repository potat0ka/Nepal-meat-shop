
# 🗄️ Database Management Guide

## 🔧 Quick Fix for Database Errors

If you're encountering database errors, run this command:

```bash
python fix_database.py
```

This will automatically:
- Fix database tables
- Create admin users
- Set up sample data
- Display login credentials

## 👤 Default User Accounts

### Admin Accounts (Full Access)
1. **Super Admin**
   - 📧 Email: `admin@meatshop.np`
   - 🔑 Password: `admin123`
   - Access: Full admin panel access

2. **Store Manager**
   - 📧 Email: `manager@meatshop.np`
   - 🔑 Password: `manager123`
   - Access: Store management features

### Customer Account (Testing)
3. **Demo Customer**
   - 📧 Email: `customer@example.com`
   - 🔑 Password: `customer123`
   - Access: Customer features only

## 🛠️ Manual Database Management

### Initialize Database
```bash
python database.py
```
Choose option 1 to initialize the database with all tables and sample data.

### Reset Database (⚠️ Deletes All Data)
```bash
python database.py
```
Choose option 2 and type `RESET` to completely reset the database.

### Check Database Status
```bash
python database.py
```
Choose option 4 to check database connection and table status.

## 📊 Database Schema

### Main Tables
- **users** - Customer and admin accounts
- **categories** - Product categories (Pork, Buffalo, etc.)
- **products** - Meat products with stock tracking
- **orders** - Customer orders
- **order_items** - Individual items in orders
- **cart_items** - Shopping cart items
- **reviews** - Product reviews and ratings
- **invoices** - Order invoices
- **delivery_areas** - Delivery zones and charges
- **stock_alerts** - Low stock notifications
- **notification_templates** - Email/SMS templates
- **notification_log** - Sent notifications log

### Key Features
- ✅ Automatic admin user creation
- ✅ Sample categories and delivery areas
- ✅ Stock management with alerts
- ✅ Order tracking and invoicing
- ✅ Email notification system
- ✅ User role management

## 🚨 Common Database Issues & Solutions

### Issue 1: "Table doesn't exist"
**Solution:** Run `python fix_database.py`

### Issue 2: "Cannot connect to database"
**Solution:** Check your DATABASE_URL environment variable

### Issue 3: "Permission denied"
**Solution:** Make sure the database file has write permissions

### Issue 4: "Admin user not found"
**Solution:** Run database initialization to create admin users

## 🔐 Security Notes

- Default passwords are for development only
- Change passwords in production
- Use environment variables for sensitive data
- Enable HTTPS in production

## 📝 Database Configuration

The application supports both SQLite (development) and PostgreSQL (production):

### SQLite (Default)
```
DATABASE_URL=sqlite:///meat_shop.db
```

### PostgreSQL (Production)
```
DATABASE_URL=postgresql://username:password@host:port/database
```

## 🧪 Testing Database

1. Run `python fix_database.py`
2. Start your application
3. Login with admin credentials
4. Test admin panel features
5. Create test orders

## 📞 Support

If you encounter issues:
1. Check the console logs
2. Run database status check
3. Try reinitializing the database
4. Check file permissions

---
**Important:** Always backup your database before making changes in production!
