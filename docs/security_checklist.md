# Security Checklist

This document outlines security best practices for managing credentials and environment variables in the Reminder App.

## Environment Variables Checklist

### General Guidelines

- [ ] Never commit `.env.*` files to source control (they should be in `.gitignore`)
- [ ] Use different `.env.*` files for each environment (development, testing, production)
- [ ] Keep backups of production environment variables in a secure location
- [ ] For production deployments, consider using a cloud secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)

### Critical Security Keys

- [ ] `SECRET_KEY`: Must be at least 32 characters, randomly generated for production
- [ ] `TWILIO_AUTH_TOKEN`: Must be stored securely and never committed to source code
- [ ] `DB_PASSWORD`: Use strong unique passwords for each environment

## Environment-Specific Requirements

### Production Environment

- [ ] Database connection must use SSL (`ssl=true` in connection string)
- [ ] `SECRET_KEY` must be at least 32 characters long
- [ ] `USE_REDIS` should be enabled for token blacklisting
- [ ] All service credentials must be valid and secure
- [ ] `CORS_ORIGINS` must include only trusted domains
- [ ] All settings validators in `ProductionSettings` class must pass
- [ ] Consider using environment variables set at the system/container level instead of .env files
- [ ] For cloud deployments, use platform-provided secrets management services

### Testing Environment

- [ ] Can use SQLite for simplified testing
- [ ] Secure services can be mocked or disabled
- [ ] Redis can be disabled
- [ ] Should not use any production credentials

### Development Environment

- [ ] Should use separate databases from production
- [ ] Can relax some validation rules for convenience
- [ ] Should still use reasonably secure credentials

## Credentials Management

### Managing Sensitive Credentials

Follow these best practices for handling sensitive credentials:

1. Store all sensitive credentials in environment variables
2. Use separate environment files for each environment (.env.development, .env.testing, .env.production)
3. Create separate accounts/projects for development and production services
4. Use test/sandbox credentials for non-production environments
5. For production systems, consider:
   - Environment variables set directly in the hosting environment
   - AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault
   - Kubernetes Secrets for container deployments
6. Periodically rotate all credentials

### Managing Twilio Credentials

Twilio is used for both SMS and WhatsApp notifications through a unified TwilioService. Secure its credentials:

1. Create a dedicated Twilio subaccount for each environment
2. Restrict API keys to only necessary capabilities
3. Store account credentials (SID, auth token) in environment variables, never in code
4. Store phone numbers in the `SenderIdentity` model, not in environment variables
5. Use environment-specific API keys (sandbox for dev/test)
6. Periodically rotate credentials in production

Important: Phone numbers used for sending SMS and WhatsApp messages are stored in the
`SenderIdentity` model with type "PHONE", not in environment variables. This allows each
user to have their own set of verified sender phone numbers.

### Sensitive Data Handling

- [ ] User passwords are hashed with bcrypt/Argon2
- [ ] Phone numbers and emails are encrypted at rest
- [ ] Personal information is validated before storage
- [ ] Access to sensitive data is logged

## Running Security Checks

The application includes built-in security checks:

```python
# Run security checks from command line
python -m app.core.security_checker
```

These checks will:

1. Validate environment files for security issues
2. Check service credentials
3. Ensure production-specific validations are enforced

## Security Validation in CI/CD

Add these steps to your CI/CD pipeline:

```yaml
# Example GitHub Action
security-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run security checks
      run: python -m app.core.security_checker
      env:
        ENV: production
        # Add other required env vars or use secrets
```

## Recommended Practices

1. **Separate Accounts**: Use separate accounts for development and production services
2. **Local Development**: Use `.env.local` (gitignored) for personal overrides
3. **Rotation Policy**: Implement a credential rotation policy for production
4. **Security Audits**: Regularly audit the `.env.production` file
5. **Access Control**: Limit access to production credentials
6. **Monitoring**: Set up alerts for unauthorized access attempts

## Environment Variables Quick Reference

| Variable | Development | Testing | Production |
|----------|------------|---------|------------|
| SQLALCHEMY_DATABASE_URI | Local MySQL | SQLite | Remote MySQL + SSL |
| SECRET_KEY | Simple key | Test key | Strong (32+ chars) |
| USE_REDIS | Optional | Disabled | Required |
| TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN | Test account | Empty/Mock | Production account |
| CORS_ORIGINS | Multiple | Multiple | Restricted |
| RATE_LIMIT | High | Disabled | Enforced |

Note: Twilio phone numbers are NOT stored in environment variables. They are stored in the `SenderIdentity` model for each user.
Note: Email/SMTP configuration is NOT stored in environment variables. It is stored in the `EmailConfiguration` model for each user.
