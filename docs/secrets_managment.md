# Secrets Management Guide

## Overview

The Reminder App uses encrypted file-based secrets management to securely store sensitive information like:

- Database credentials
- API keys and tokens
- Service account credentials
- Security keys

This approach is more secure than storing these values in plain text environment variables.

## How It Works

1. Secrets are stored in encrypted files in the `./secrets/` directory
2. Files are named by environment: `secrets.{env}.enc` (e.g., `secrets.development.enc`)
3. Encryption uses the application's `encryption_service` with the `SECRET_KEY`
4. Secrets are organized by category (database, security, etc.)
5. The application loads secrets automatically at startup
6. Falls back to environment variables if secrets are not found

## Secret Categories

Secrets are organized into these categories:

- `database`: Database credentials (host, port, user, password, name)
- `security`: Security keys (secret_key, dev_secret_key)
- `email`: Email service credentials (SMTP settings)
- `sms`: SMS service credentials (Twilio settings)
- `whatsapp`: WhatsApp API credentials
- `payment`: Payment processor credentials (Stripe)
- `s3`: AWS S3 storage credentials

## Managing Secrets

### Initializing Secrets

For a new environment, initialize the secrets structure:

```bash
# Initialize development environment (default)
python scripts/manage_secrets.py --init

# Initialize testing environment 
python scripts/manage_secrets.py --env testing --init

# Initialize production environment
python scripts/manage_secrets.py --env production --init