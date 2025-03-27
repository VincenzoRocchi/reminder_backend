# AWS Deployment Guide

This document provides instructions for deploying the Reminder App API to AWS Elastic Beanstalk.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured
3. EB CLI installed (`pip install awsebcli`)
4. Git repository set up

## Environment Setup

The application is designed to run in three environments:

1. **Testing**: Local SQLite database, local server
2. **Development**: AWS deployment with RDS MySQL, S3 storage (development/staging)
3. **Production**: AWS deployment with RDS MySQL, S3 storage (production)

## AWS Services Used

- **Elastic Beanstalk**: Application hosting
- **RDS**: MySQL database
- **S3**: File storage
- **ElastiCache**: Redis (optional)
- **IAM**: Access control
- **CloudWatch**: Monitoring and logging

## Initial Setup

### 1. Create RDS Instances

Create separate RDS MySQL instances for development and production:

```bash
# Example AWS CLI command for development RDS
aws rds create-db-instance \
    --db-instance-identifier reminder-app-dev \
    --db-instance-class db.t3.micro \
    --engine mysql \
    --master-username dev_user \
    --master-user-password dev_password \
    --allocated-storage 20 \
    --db-name reminder_app_dev

# Example AWS CLI command for production RDS
aws rds create-db-instance \
    --db-instance-identifier reminder-app-prod \
    --db-instance-class db.t3.small \
    --engine mysql \
    --master-username prod_user \
    --master-user-password prod_strong_password \
    --allocated-storage 20 \
    --db-name reminder_app_prod \
    --backup-retention-period 7 \
    --multi-az
```

Update the `.env.development` and `.env.production` files with the RDS endpoints.

### 2. Create S3 Buckets

Create separate S3 buckets for development and production:

```bash
# Example AWS CLI command for development S3
aws s3api create-bucket \
    --bucket dev-reminder-app-bucket \
    --region us-east-1

# Example AWS CLI command for production S3
aws s3api create-bucket \
    --bucket prod-reminder-app-bucket \
    --region us-east-1
```

Update the `.env.development` and `.env.production` files with the S3 bucket names.

### 3. Create IAM Roles

Create IAM roles with appropriate policies for S3 access and other AWS services.

### 4. Initialize Elastic Beanstalk Application

```bash
# Initialize EB application
eb init

# Create development environment
eb create reminder-app-dev --envvars ENV=development

# Create production environment
eb create reminder-app-prod --envvars ENV=production
```

## Deployment Instructions

### Development Deployment

To deploy to the development environment:

```bash
git checkout develop
eb use reminder-app-dev
eb deploy
```

### Production Deployment

To deploy to the production environment:

```bash
git checkout main
eb use reminder-app-prod
eb deploy
```

## Environment Variables

The necessary environment variables are set in the `.ebextensions/01_environment.config` file. For sensitive information, use AWS Systems Manager Parameter Store or AWS Secrets Manager.

## Troubleshooting

1. Check EB logs: `eb logs`
2. SSH into EB instance: `eb ssh`
3. View environment status: `eb status`
4. View environment health: `eb health`

## Security Best Practices

1. Use IAM roles instead of hardcoded AWS credentials
2. Enable HTTPS for all endpoints
3. Restrict database access to EB security group
4. Use private S3 buckets with appropriate permissions
5. Rotate secrets regularly
6. Configure proper logging and monitoring 