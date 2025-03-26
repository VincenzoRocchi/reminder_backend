# scripts/manage_secrets.py
#!/usr/bin/env python
import os
import sys
import json
import argparse
from pathlib import Path
from getpass import getpass
import secrets as py_secrets

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment before importing app modules
parser = argparse.ArgumentParser(description="Manage application secrets")
parser.add_argument("--env", default="development", 
                  help="Environment (development, testing, production)")
args, unknown = parser.parse_known_args()

# Set environment
os.environ["ENV"] = args.env

# Now import app modules
from app.core.encryption import encryption_service
from app.core.exceptions import EncryptionError, AppException

def load_existing_secrets(env):
    """Load existing secrets if available"""
    secrets_path = Path(f"./secrets/secrets.{env}.enc")
    if not secrets_path.exists():
        return False
        
    try:
        with open(secrets_path, "r") as f:
            encrypted_data = f.read().strip()
        
        if not encrypted_data:
            return False
            
        # Just try to decrypt - we don't need the actual content here
        encryption_service.decrypt_string(encrypted_data)
        return True
    except Exception as e:
        print(f"Error checking existing secrets: {str(e)}")
        return False

def initialize_secrets(env):
    """Initialize default secrets for environment"""
    if env == "development":
        # Setup development secrets
        # Generate a secure random key for development
        dev_secret_key = py_secrets.token_urlsafe(32)
        
        secrets = {
            "database": {
                "host": "localhost",
                "port": "3306",
                "user": "dev_user",
                "password": "dev_password",
                "name": "reminder_app_dev"
            },
            "security": {
                "secret_key": dev_secret_key,
                "dev_secret_key": dev_secret_key
            },
            "email": {
                "smtp_host": "smtp.mailtrap.io",
                "smtp_port": "587",
                "smtp_user": "your_mailtrap_user",
                "smtp_password": "your_mailtrap_password",
                "email_from": "dev@reminderapp.com"
            },
            "sms": {
                "twilio_account_sid": "your_twilio_test_sid",
                "twilio_auth_token": "your_twilio_test_token",
                "twilio_phone_number": "your_twilio_test_phone"
            },
            "payment": {
                "stripe_api_key": "your_stripe_test_key",
                "stripe_webhook_secret": "your_stripe_webhook_test_secret"
            }
        }
        
        print("Initializing development environment secrets...")
        
    elif env == "testing":
        # Testing secrets - similar but with test values
        secrets = {
            "database": {
                "host": "localhost", 
                "port": "3306",
                "user": "test_user",
                "password": "test_password",
                "name": "reminder_app_test"
            },
            "security": {
                "secret_key": "test-secret-key-for-testing-only"
            }
        }
        
        print("Initializing testing environment secrets...")
        
    elif env == "production":
        # For production, create only the structure with empty values
        # You'll need to fill these in with real values
        secrets = {
            "database": {},
            "security": {},
            "email": {},
            "sms": {},
            "payment": {},
            "s3": {}
        }
        
        print("Creating empty structure for production secrets...")
        print("Please set actual production values using --set or --set-password")
        
    else:
        print(f"Unknown environment: {env}")
        return False
    
    # Save to encrypted secrets file
    try:
        # Create directory if it doesn't exist
        secrets_dir = Path("./secrets")
        secrets_dir.mkdir(exist_ok=True)
        
        # Encrypt and save
        secrets_json = json.dumps(secrets)
        encrypted_data = encryption_service.encrypt_string(secrets_json)
        
        with open(f"./secrets/secrets.{env}.enc", "w") as f:
            f.write(encrypted_data)
            
        print(f"Successfully initialized secrets for {env} environment")
        return True
        
    except Exception as e:
        print(f"Error saving secrets: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Manage application secrets")
    parser.add_argument("--env", default="development", 
                      help="Environment (development, testing, production)")
    parser.add_argument("--set", nargs=3, action="append", metavar=("CATEGORY", "KEY", "VALUE"),
                      help="Set a secret value (can be used multiple times)")
    parser.add_argument("--set-password", nargs=2, action="append", metavar=("CATEGORY", "KEY"),
                      help="Set a secret value, prompting for input (for passwords)")
    parser.add_argument("--get", nargs=2, metavar=("CATEGORY", "KEY"),
                      help="Get a specific secret value")
    parser.add_argument("--list", action="store_true", 
                      help="List all secret keys (without values)")
    parser.add_argument("--init", action="store_true", 
                      help="Initialize with default secrets for environment")
    parser.add_argument("--import-file", 
                      help="Import secrets from JSON file")
    parser.add_argument("--export-file", 
                      help="Export secrets to JSON file (unencrypted - handle with care!)")
    
    args = parser.parse_args()
    
    # Now import the secrets manager - we do this after argument parsing
    # to ensure the environment is set correctly
    from app.core.secrets_manager import secrets_manager
    
    # Initialize if requested or if secrets don't exist
    secrets_exist = load_existing_secrets(args.env)
    if args.init or not secrets_exist:
        if not initialize_secrets(args.env):
            return 1
    
    # Get a specific secret if requested
    if args.get:
        category, key = args.get
        try:
            value = secrets_manager.get_secret(category, key)
            if value is not None:
                print(f"{category}.{key} = {value}")
            else:
                print(f"Secret {category}.{key} not found")
        except AppException as e:
            print(f"Error: {e.message}")
            return 1
    
    # Set secrets if provided
    if args.set:
        for category, key, value in args.set:
            try:
                secrets_manager.set_secret(category, key, value)
                print(f"Set {category}.{key}")
            except AppException as e:
                print(f"Error setting {category}.{key}: {e.message}")
                return 1
    
    # Set password secrets if provided (with prompt)
    if args.set_password:
        for category, key in args.set_password:
            # Prompt for password without echo
            value = getpass(f"Enter value for {category}.{key}: ")
            try:
                secrets_manager.set_secret(category, key, value)
                print(f"Set {category}.{key}")
            except AppException as e:
                print(f"Error setting {category}.{key}: {e.message}")
                return 1
    
    # Import from file if requested
    if args.import_file:
        try:
            with open(args.import_file, "r") as f:
                import_data = json.load(f)
            
            # Import each category/value
            for category, values in import_data.items():
                for key, value in values.items():
                    try:
                        secrets_manager.set_secret(category, key, value)
                        print(f"Imported {category}.{key}")
                    except Exception as e:
                        print(f"Error importing {category}.{key}: {str(e)}")
            
        except Exception as e:
            print(f"Error importing from file: {str(e)}")
            return 1
    
    # Export to file if requested
    if args.export_file:
        try:
            # Build the secrets dictionary
            export_data = {}
            
            # Get all categories and secrets
            categories = [
                "database", "security", "email", "sms", 
                "payment", "s3"
            ]
            
            for category in categories:
                try:
                    category_data = secrets_manager.get_category(category)
                    if category_data:
                        export_data[category] = category_data
                except Exception:
                    pass
            
            # Export to file
            with open(args.export_file, "w") as f:
                json.dump(export_data, f, indent=2)
                
            print(f"Exported secrets to {args.export_file}")
            print("WARNING: This file contains unencrypted secrets. Handle with care!")
            
        except Exception as e:
            print(f"Error exporting to file: {str(e)}")
            return 1
    
    # List secrets if requested
    if args.list:
        try:
            # Get all categories and secrets
            categories = [
                "database", "security", "email", "sms", 
                "payment", "s3"
            ]
            
            print(f"Secrets for {args.env} environment:")
            for category in categories:
                try:
                    category_data = secrets_manager.get_category(category)
                    if category_data:
                        print(f"  {category}:")
                        for key in category_data.keys():
                            print(f"    - {key}")
                except Exception:
                    # Skip categories that don't exist
                    pass
                    
        except Exception as e:
            print(f"Error listing secrets: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())