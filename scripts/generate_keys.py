#!/usr/bin/env python
"""
Key Generator for Reminder App

This script generates secure keys that can be used for various security purposes
in the application, including SECRET_KEY, DEV_SECRET_KEY, and other credentials.

Usage:
  python generate_keys.py
  python generate_keys.py --length 64
  python generate_keys.py --key-type jwt
"""

import argparse
import secrets
import string
import sys
import random

def generate_urlsafe_key(length=32):
    """Generate a URL-safe base64-encoded random key."""
    # Each byte becomes approximately 1.3 characters in base64
    # So we generate slightly more bytes than requested length
    bytes_needed = max(1, int(length * 0.75))
    return secrets.token_urlsafe(bytes_needed)[:length]

def generate_alphanumeric_key(length=32):
    """Generate an alphanumeric key with special characters."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_key(length=64):
    """Generate a key suitable for JWT signing."""
    return generate_urlsafe_key(length)

def generate_api_key(length=32):
    """Generate an API key format."""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
    key_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length - 4))
    return f"{prefix}_{key_part}"

def print_key_with_instructions(key, key_type, var_name):
    """Print the generated key with instructions for use."""
    print(f"\n{'-' * 60}")
    print(f"Generated {key_type} ({len(key)} characters):")
    print(f"{'-' * 60}")
    print(key)
    print(f"{'-' * 60}")
    print(f"Add this to your .env file:")
    print(f"{var_name}={key}")
    print(f"{'-' * 60}\n")

def main():
    parser = argparse.ArgumentParser(description="Generate secure keys for Reminder App")
    parser.add_argument('--length', type=int, default=32, help='Length of the key (default: 32)')
    parser.add_argument('--key-type', choices=['secret', 'urlsafe', 'alphanumeric', 'jwt', 'api'], 
                      default='secret', help='Type of key to generate (default: secret)')
    
    args = parser.parse_args()
    
    key_type = args.key_type
    length = args.length
    
    if key_type == 'secret' or key_type == 'urlsafe':
        key = generate_urlsafe_key(length)
        var_name = "SECRET_KEY"
    elif key_type == 'alphanumeric':
        key = generate_alphanumeric_key(length)
        var_name = "SECRET_KEY"
    elif key_type == 'jwt':
        key = generate_jwt_key(length)
        var_name = "SECRET_KEY"
    elif key_type == 'api':
        key = generate_api_key(length)
        var_name = "API_KEY"
    else:
        print(f"Unknown key type: {key_type}")
        return 1
    
    print_key_with_instructions(key, key_type, var_name)
    
    # Print example usage
    print("Usage examples:")
    print("  Generate a default secret key:")
    print("    python generate_keys.py")
    print("\n  Generate a longer JWT key:")
    print("    python generate_keys.py --length 64 --key-type jwt")
    print("\n  Generate an API key:")
    print("    python generate_keys.py --key-type api")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())