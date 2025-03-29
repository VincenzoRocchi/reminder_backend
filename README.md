# Reminder App

A comprehensive backend system for businesses (such as accounting firms) to manage and send reminders to their clients via email, SMS, and WhatsApp.

## Features

- **User & Client Management**: Register, authenticate, and manage business users and their clients
- **Business Management**: Create and manage business accounts with customized settings
- **Reminder System**: Set up one-time or recurring reminders with different types (deadlines, notifications, etc.)
- **Multi-channel Notifications**: Send reminders via email, SMS, or WhatsApp
- **Scheduling**: Automated reminder delivery at specified times with manual trigger option
- **Dashboard & Analytics**: Monitor notification history and status
- **Error Handling**: Robust error handling for notification delivery
- **Event-Driven Architecture**: Centralized event system for tracking and monitoring application events

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | FastAPI (Python 3.11+) |
| **Database** | SQL Databases (MySQL/PostgreSQL/SQLite) via SQLAlchemy |
| **ORM** | SQLAlchemy 2.0+ |
| **Migrations** | Alembic |
| **Notifications** | SMTP (Email), Twilio (SMS), WhatsApp API |
| **Deployment** | AWS Elastic Beanstalk, Docker |
| **Task Scheduling** | APScheduler (integrated in application) |
| **Caching** | Redis |
| **Authentication** | JWT (OAuth2) with Passlib & JOSE |
| **API Documentation** | Swagger/OpenAPI (built-in with FastAPI) |
| **Testing** | Pytest, pytest-asyncio |
| **Configuration** | Environment-based with python-dotenv |

## Project Structure

```bash
reminder_backend/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies 
├── pyproject.toml             # Modern Python project configuration
├── main.py                    # Application entry point
├── Procfile                   # Process file for AWS Elastic Beanstalk
├── app/                       # Main application package
│   ├── main.py                # FastAPI application initialization
│   ├── database.py            # Database connection and session management
│   ├── __init__.py            # Package initialization with version
│   ├── api/                   # API endpoints
│   │   ├── endpoints/         # Route handlers by resource
│   │   ├── dependencies.py    # API dependencies (auth, etc.)
│   │   └── routes.py          # API router configuration
│   ├── core/                  # Core functionality
│   │   ├── security/          # Authentication & authorization
│   │   ├── middleware/        # Custom middleware components
│   │   ├── exception_handlers.py # Global exception handlers
│   │   ├── security_checker.py # Security validation at startup
│   │   ├── logging_setup.py   # Logging configuration
│   │   └── settings.py        # Environment-based configuration
│   ├── events/                # Event-driven components
│   │   ├── persistence.py     # Event storage
│   │   ├── monitoring.py      # Event monitoring endpoints
│   │   └── __init__.py        # Event system setup
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── users.py           # User models
│   │   ├── clients.py         # Client models
│   │   ├── reminders.py       # Reminder models
│   │   └── ...                # Other data models
│   ├── repositories/          # Data access layer
│   │   ├── user.py            # User data operations
│   │   ├── client.py          # Client data operations
│   │   └── ...                # Other data repositories
│   ├── schemas/               # Pydantic schemas for validation
│   │   ├── users.py           # User schemas
│   │   ├── clients.py         # Client schemas
│   │   └── ...                # Other schemas
│   └── services/              # Business logic & external integrations
│       ├── user.py            # User service
│       ├── client.py          # Client service
│       ├── reminder.py        # Reminder service
│       ├── senderIdentity.py  # Sender identity management
│       ├── notification.py    # Notification orchestration
│       ├── email_service.py   # Email notification service
│       ├── twilio_service.py  # SMS notification via Twilio
│       ├── scheduler_service.py # Background task scheduling
│       └── auth_service.py    # Authentication service
├── env/                       # Environment configuration directory
│   ├── .env.example           # Example environment variables
│   └── README.md              # Environment setup instructions
├── scripts/                   # Utility scripts
│   └── admin_setup.example.py # Template for admin configuration
├── .elasticbeanstalk/         # AWS Elastic Beanstalk configuration
├── .ebextensions/             # AWS EB deployment configurations
├── logs/                      # Application logs directory
└── docs/                      # Extended documentation
```

## Architecture

The application follows a layered architecture with clear separation of concerns:

### API Layer

- **Endpoints**: Handle HTTP requests and responses
- **Dependencies**: Shared components like authentication
- **Routes**: API routing configuration

### Service Layer

- **Business Logic**: Core application functionality
- **External Services**: Integration with email, SMS, etc.
- **Scheduling**: Background tasks and reminder processing

### Repository Layer

- **Data Access**: Abstraction over database operations
- **Query Logic**: Complex data retrieval patterns
- **Transaction Management**: Ensuring data consistency

### Model Layer

- **Database Models**: SQLAlchemy ORM definitions
- **Schemas**: Pydantic models for validation and serialization
- **Domain Objects**: Business entities and relationships

### Event System

- **Event Tracking**: Records system events
- **Event Persistence**: Stores events for traceability
- **Monitoring**: Admin endpoints for event analysis

### Core Components

- **Settings**: Environment-specific configuration
- **Security**: Authentication, authorization, and encryption
- **Middleware**: Custom request processing
- **Exception Handlers**: Centralized error handling

## Deployment Architecture

The Reminder App is designed for deployment on AWS Elastic Beanstalk with the following components:

- **App Server**: Elastic Beanstalk with auto-scaling capabilities
- **Database**: SQL database (MySQL in production via RDS)
- **Caching**: Redis for improved performance
- **Load Balancing**: Application Load Balancer
- **Monitoring**: CloudWatch for logs and metrics
- **Security**: WAF, Security Groups, and IAM roles

For high-availability deployments, the architecture includes:

- **Multi-AZ Database**: For database redundancy
- **Auto-scaling**: To handle variable load
- **Backup Strategy**: Regular database snapshots
- **Security Layers**: Including WAF protection and secure credentials management

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL database (or SQLite for development/testing)
- AWS account for production deployment
- Twilio account (for SMS)
- SMTP server (for Email)
- WhatsApp Business API access

### Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/reminder-backend.git
cd reminder-backend
```

#### 2. Set Up a Virtual Environment

Using venv:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Or using uv (faster):

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies

Using pip:

```bash
pip install -r requirements.txt
```

Or using pyproject.toml (recommended):

```bash
pip install -e ".[dev]"
```

#### 4. Set Up Environment Configuration

1. Copy the example environment file:

   ```bash
   cp env/.env.example env/.env
   ```

2. Edit the `.env` file to configure:
   - Database connections
   - API keys (AWS, Stripe, etc.)
   - Server settings (detailed below)
   - Other environment-specific settings

### Server Configuration

Configure server behavior by setting these environment variables in your `.env` file:

```env
# Basic server settings
SERVER_HOST=0.0.0.0        # Host to bind the server to (use 127.0.0.1 for local-only access)
SERVER_PORT=8000           # Port to run the server on
SERVER_WORKERS=4           # Number of worker processes (set to 1 for debugging)
SERVER_RELOAD=false        # Set to true during development for auto-reload

# Environment settings
ENVIRONMENT=development    # Options: development, testing, production
LOG_LEVEL=INFO             # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Different environments have different recommended settings:

- **Development**: Enable auto-reload and debugging

  ```env
  SERVER_HOST=127.0.0.1
  SERVER_WORKERS=1
  SERVER_RELOAD=true
  LOG_LEVEL=DEBUG
  ```

- **Testing**: Use minimal configuration

  ```env
  SERVER_HOST=127.0.0.1
  SERVER_WORKERS=1
  SQL_ECHO=true            # For debugging SQL queries
  ```

- **Production**: Optimize for performance and security

  ```env
  SERVER_HOST=0.0.0.0
  SERVER_WORKERS=4         # Or more based on CPU cores
  SERVER_RELOAD=false
  SECURE_COOKIES=true
  SSL_ENABLED=true
  ```

#### 5. Configure Admin User

1. Copy the admin setup example file:

   ```bash
   cp scripts/admin_setup.example.py scripts/admin_setup.py
   ```

2. Edit `scripts/admin_setup.py` with your desired admin credentials:

   ```python
   ADMIN_CONFIG = {
       'username': 'admin',                  # Change this to your admin username
       'email': 'admin@example.com',         # Change this to your admin email
       'password': 'change-this-password',   # Use a strong, secure password
       'first_name': 'Admin',                # Your first name
       'last_name': 'User',                  # Your last name
       'business_name': 'Admin Business',    # Your business name
       'phone_number': '+123456789',         # Your phone number
       'is_active': True,                    # Keep this True
       'is_superuser': True                  # Keep this True for admin privileges
   }
   ```

3. The application will automatically use these settings when creating the admin user.

#### 6. Run the Application

You can run the application using one of the following methods:

#### Option 1: Using Python

```bash
python app/main.py
```

#### Option 2: Using Uvicorn directly

```bash
uvicorn app.main:app --host ${SERVER_HOST} --port ${SERVER_PORT} --workers ${SERVER_WORKERS} --reload ${SERVER_RELOAD}
```

Where the environment variables are set in your `.env` file or can be passed directly:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --reload
```

Once running, you can access:

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Admin Dashboard: [http://localhost:8000/admin](http://localhost:8000/admin)
- Login with your configured admin credentials

### Testing Setup

#### 1. Configure Testing Environment

```bash
# Create testing environment file
cp env/.env.example env/.env.testing

# Important settings for testing:
# SQLALCHEMY_DATABASE_URI=sqlite:///./test.db
# DISABLE_SCHEDULER=false  # Will only run if reminders exist
```

#### 2. Run Tests

```bash
# Set environment
export ENV=testing  # Linux/Mac
set ENV=testing     # Windows CMD
$env:ENV = "testing"  # PowerShell

# Run tests
pytest
```

### Production Deployment

#### 1. Configure Production Environment

```bash
# Create production environment file securely
cp env/.env.example env/.env.production

# Configure all required settings for production:
# - Strong SECRET_KEY
# - Production database credentials
# - Twilio credentials
# - CORS settings
# - SSL configuration
```

#### 2. AWS Elastic Beanstalk Deployment

The application is configured for deployment on AWS Elastic Beanstalk:

1. Install AWS EB CLI:

   ```bash
   pip install awsebcli
   ```

2. Initialize Elastic Beanstalk (if not already done):

   ```bash
   eb init
   ```

3. Deploy to Elastic Beanstalk:

   ```bash
   eb deploy
   ```

4. Open the deployed application:

   ```bash
   eb open
   ```

The deployment uses the following configuration:

- `.elasticbeanstalk/config.yml` - Environment configuration
- `.ebextensions/` - Deployment customization
- `Procfile` - Process specification using Gunicorn with Uvicorn workers

#### 3. Manual Docker Deployment

Alternatively, you can use Docker for deployment:

```bash
# Build the Docker image
docker build -t reminder-backend:latest .

# Run with Docker
docker run -p 8000:8000 --env-file env/.env.production reminder-backend:latest
```

#### 4. Monitor Logs

Access logs via Elastic Beanstalk:

```bash
eb logs
```

Or directly in CloudWatch via the AWS Console.

## Environment Configuration

The application supports multiple environments through configuration files:

### Configuration Types

- **Development** (`ENV=development`): For local development with debugging features enabled
- **Testing** (`ENV=testing`): For automated tests with SQLite and minimal external dependencies
- **Production** (`ENV=production`): For deployed instances with security features and optimizations

### Environment Selection

The application can be started with a specific environment in several ways:

1. Using the entry point script (interactive):

   ```bash
   python main.py
   # Then select: 1) Development, 2) Production, or 3) Testing
   ```

2. Setting the ENV variable before running:

   ```bash
   # Linux/Mac
   export ENV=development
   python -m app.main
   
   # Windows
   set ENV=development
   python -m app.main
   ```

3. Directly with Uvicorn:

   ```bash
   ENV=development uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Security Features

The application implements several security features:

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt-based password protection
- **Role-Based Access Control**: Admin/User role separation
- **HTTPS Enforcement**: Automatic HTTPS redirection in production
- **Security Headers**: Protection against common web vulnerabilities
- **Trusted Host Validation**: Request host validation in production
- **JSON Sanitization**: Protection against JSON-based attacks
- **Startup Security Checks**: Validation of critical security settings

## Event Tracking System

The application includes an event system for tracking important operations:

- **Event Recording**: Captures key application events
- **Event Storage**: Persists events for audit purposes
- **Event Monitoring**: Admin interface for reviewing events
- **Event Recovery**: Ability to recover and replay events
