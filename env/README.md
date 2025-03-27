# Environment Configuration Directory

This directory contains all environment configuration files for the application.

## Files Structure

The application looks for environment files in this directory only:

- `env/.env.development` - Development environment settings
- `env/.env.testing` - Testing environment settings
- `env/.env.production` - Production environment settings
- `env/.env` - (Optional) Fallback for all environments

## Environment Types

The application uses different environment files based on the `ENV` environment variable:

- `ENV=development` - Development environment (local)
- `ENV=testing` - Testing environment (automated tests)
- `ENV=production` - Production environment (deployed)

## Creating Environment Files

Create your environment-specific configuration by starting with a template:

```bash
# Copy from the example environment template
cp env/.env.example env/.env.development
cp env/.env.example env/.env.production

# Then modify each file according to the specific environment needs
```

## Security Note

**IMPORTANT:** Never commit these environment files with sensitive information to version control. 
These files contain database credentials, API keys, and other sensitive information. 