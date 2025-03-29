"""
Admin Setup Configuration

This file contains the default admin user settings for the reminder application.

HOW TO USE:
1. COPY this file to scripts/admin_setup.py (without the .example suffix)
2. MODIFY the settings below with your own secure admin credentials
3. The application will automatically use these settings when creating the admin user

SECURITY NOTES:
- The scripts/admin_setup.py file should NEVER be committed to version control!
- It is already added to .gitignore to prevent accidental commits
- Always use a strong, unique password for admin accounts
- In production environments, consider changing these credentials regularly

If scripts/admin_setup.py is not found, the application will fall back to default
credentials (admin/admin), which are insecure for production use.
"""

# =======================================================================
# Default admin user configuration
# =======================================================================
# Modify these values with your own secure admin credentials
ADMIN_CONFIG = {
    'username': 'admin',                  # Admin username for login
    'email': 'admin@example.com',         # Admin email address
    'password': 'change-this-password',   # CHANGE THIS to a secure password!
    'first_name': 'Admin',                # Admin first name
    'last_name': 'User',                  # Admin last name
    'business_name': 'Admin Business',    # Admin business name
    'phone_number': '+123456789',         # Admin phone number
    'is_active': True,                    # Whether admin account is active
    'is_superuser': True                  # Must be True for admin privileges
}

# =======================================================================
# Credentials file settings
# =======================================================================
# Whether to create a file with the admin credentials for reference
# Set to False if you don't want to store credentials in a file
CREATE_CREDENTIALS_FILE = True

# Path where admin credentials will be saved for reference
# This file is also listed in .gitignore for security
CREDENTIALS_FILE_PATH = "admin_credentials.txt" 