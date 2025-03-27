# AWS Secrets Manager Integration Guide

## About This Guide

This guide provides instructions for setting up AWS Secrets Manager to handle sensitive credentials in production environments. Currently, the application uses environment variables, but AWS Secrets Manager should be considered for production deployments to enhance security.

## Why Use AWS Secrets Manager?

- **Centralized Credential Management**: All sensitive information in one secure place
- **Automatic Rotation**: Credentials can be automatically rotated without downtime
- **Fine-grained Access Control**: IAM policies control who can access which secrets
- **Encryption**: All secrets are encrypted at rest using AWS KMS
- **Audit Trail**: All access is logged and can be monitored
- **Compliance**: Helps meet regulatory requirements

## Implementation Steps

### 1. AWS Setup

#### Create AWS Account

If you don't have an AWS account, create one at [aws.amazon.com](https://aws.amazon.com/).

#### Install AWS CLI

```bash
# Install AWS CLI
pip install awscli

# Configure with your credentials
aws configure
```

#### Create Secrets

```bash
# Create a secret for production environment
aws secretsmanager create-secret \
    --name reminder-app/production \
    --description "Production credentials for Reminder App" \
    --secret-string '{
        "SECRET_KEY": "your-strong-production-secret-key",
        "DB_PASSWORD": "your-strong-database-password",
        "TWILIO_ACCOUNT_SID": "your-twilio-account-sid",
        "TWILIO_AUTH_TOKEN": "your-twilio-auth-token"
    }'
```

#### Set Up IAM Roles and Permissions

1. Create an IAM role for your application
2. Attach a policy with the following permissions:

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "secretsmanager:GetSecretValue"
               ],
               "Resource": "arn:aws:secretsmanager:*:*:secret:reminder-app/*"
           }
       ]
   }
   ```

### 2. Application Integration

#### Install Required Packages

```bash
pip install boto3
```

#### Create AWS Secrets Manager Adapter

Create a new file `app/core/aws_secrets_manager.py`:

```python
import boto3
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AWSSecretsManager:
    def __init__(self, environment: str = "development"):
        """
        Initialize the AWS Secrets Manager client.
        
        Args:
            environment: The environment (development, testing, production)
        """
        self.environment = environment
        self.secret_name = f"reminder-app/{environment}"
        
        # Initialize the client (uses AWS credentials from environment or IAM role)
        self.client = boto3.client('secretsmanager')
        self._secrets_cache = None
    
    def get_secrets(self) -> Dict[str, Any]:
        """
        Retrieve all secrets for the current environment.
        
        Returns:
            Dictionary of secrets
        """
        # Use cached secrets if available
        if self._secrets_cache is not None:
            return self._secrets_cache
            
        try:
            # Get the secret from AWS Secrets Manager
            response = self.client.get_secret_value(SecretId=self.secret_name)
            
            # Parse the secret string
            if 'SecretString' in response:
                self._secrets_cache = json.loads(response['SecretString'])
                return self._secrets_cache
            else:
                logger.warning(f"No text secret found for {self.secret_name}")
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving secrets from AWS: {str(e)}")
            return {}
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a specific secret value.
        
        Args:
            key: The secret key to retrieve
            
        Returns:
            The secret value or None if not found
        """
        secrets = self.get_secrets()
        return secrets.get(key)
```

#### Update Settings to Use AWS Secrets Manager

Modify your settings initialization code to use AWS Secrets Manager in production:

```python
# In app/core/settings/base.py or appropriate initialization file

# Only for production, use AWS Secrets Manager
if ENV == "production":
    try:
        # Import the AWS Secrets Manager
        from app.core.aws_secrets_manager import AWSSecretsManager
        
        # Get secrets for the current environment
        secrets_manager = AWSSecretsManager(ENV)
        secrets = secrets_manager.get_secrets()
        
        # Override environment variables with secrets
        if secrets:
            # Critical settings that should be overridden
            critical_settings = [
                "SECRET_KEY", 
                "DB_PASSWORD", 
                "TWILIO_ACCOUNT_SID", 
                "TWILIO_AUTH_TOKEN"
            ]
            
            for key in critical_settings:
                if key in secrets:
                    os.environ[key] = secrets[key]
                    
            logger.info("Successfully loaded secrets from AWS Secrets Manager")
    except Exception as e:
        logger.warning(f"Failed to load AWS Secrets: {str(e)}. Using environment variables.")
```

### 3. Secret Rotation

AWS Secrets Manager supports automatic rotation of secrets:

1. In the AWS Console, navigate to the secret
2. Click "Edit rotation"
3. Enable automatic rotation and set a schedule
4. Create a Lambda function to handle the rotation logic

For detailed information, refer to [AWS documentation on secret rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html).

## Best Practices

1. **Environment Separation**: Use different secrets for different environments
2. **Least Privilege**: Grant only necessary permissions to access secrets
3. **Monitoring**: Set up CloudWatch alerts for suspicious access patterns
4. **Backup**: Keep a secure backup of production credentials outside AWS
5. **Documentation**: Document all secrets and their purpose

## Troubleshooting

1. **Access Denied Errors**: Check IAM permissions for your application
2. **Region Issues**: Ensure you're accessing the correct AWS region
3. **Version Problems**: Secrets have versions; make sure you're accessing the current one
4. **Credential Chain**: AWS SDK looks for credentials in environment, then ~/.aws, then IAM role

## Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [Boto3 Secrets Manager Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [AWS IAM Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)
