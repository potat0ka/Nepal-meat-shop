# Scripts Directory

This directory contains utility and deployment scripts for the Nepal Meat Shop platform.

## Utility Scripts

### `check_session.py`
Checks the current user session and login status.
```bash
python scripts/check_session.py
```

### `create_admin.py`
Creates an initial admin user for the application.
```bash
python scripts/create_admin.py
```

### `list_users.py`
Lists all users in the database.
```bash
python scripts/list_users.py
```

## Deployment Scripts

### `deploy.bat` (Windows)
Windows batch script for deployment.
```cmd
scripts\deploy.bat
```

### `deploy.ps1` (PowerShell)
PowerShell script for deployment.
```powershell
.\scripts\deploy.ps1
```

### `deploy.sh` (Linux/macOS)
Bash script for deployment.
```bash
./scripts/deploy.sh
```

## Usage Notes

- All scripts should be run from the project root directory
- Ensure MongoDB is running before executing database-related scripts
- Make sure environment variables are properly configured in `.env.mongo`