# Reminder App

A comprehensive backend system for businesses (such as accounting firms) to manage and send reminders to their clients via email, SMS, and WhatsApp, with integrated payment capabilities.

## Features

- **User & Client Management**: Register, authenticate, and manage business users and their clients
- **Business Management**: Create and manage business accounts with customized settings
- **Reminder System**: Set up one-time or recurring reminders with different types (deadlines, payments, etc.)
- **Multi-channel Notifications**: Send reminders via email, SMS, or WhatsApp
- **Scheduling**: Automated reminder delivery at specified times with manual trigger option
- **Payment Integration**: Include payment links (Stripe) in reminders for easy client transactions
- **Dashboard & Analytics**: Monitor notification history and payment status
- **Error Handling**: Robust error handling for notification delivery and payment processing

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | FastAPI (Python) |
| **Database** | AWS RDS (MySQL) |
| **ORM** | SQLAlchemy |
| **Migrations** | Alembic |
| **Notifications** | SMTP (Email), Twilio (SMS), WhatsApp Business API |
| **Payment Processing** | Stripe API |
| **Deployment** | Docker + AWS EC2/ECS |
| **Load Balancing** | AWS Application Load Balancer |
| **Task Scheduling** | APScheduler (integrated in application) |
| **Authentication** | JWT (OAuth2) |
| **API Documentation** | Swagger/OpenAPI |
| **Testing** | Pytest |

## Project Structure

```bash
reminder_backend/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── env/                       # Environment configuration directory
│   ├── .env.example           # Example environment variables
│   ├── .env.development       # Development environment variables
│   ├── .env.testing           # Testing environment variables
│   ├── .env.production        # Production environment variables
│   └── README.md              # Environment setup instructions
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── main.py                    # Application entry point
├── alembic/                   # Database migrations
├── app/                       # Main application package
│   ├── api/                   # API endpoints
│   │   ├── endpoints/         # Route handlers by resource
│   │   ├── dependencies.py    # API dependencies (auth, etc.)
│   │   └── routes.py          # API router configuration
│   ├── core/                  # Core functionality
│   │   ├── security/          # Authentication & authorization
│   │   ├── encryption.py      # Data encryption utilities
│   │   ├── exceptions.py      # Custom exception types
│   │   └── settings/          # Environment-based configuration
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── users.py           # User models
│   │   ├── clients.py         # Client models
│   │   ├── reminders.py       # Reminder models
│   │   ├── notifications.py   # Notification models
│   │   └── ...                # Other data models
│   ├── repositories/          # Data access layer
│   │   ├── user.py            # User data operations
│   │   ├── client.py          # Client data operations
│   │   ├── reminder.py        # Reminder data operations
│   │   └── ...                # Other data repositories
│   ├── schemas/               # Pydantic schemas for validation
│   │   ├── users.py           # User schemas
│   │   ├── clients.py         # Client schemas
│   │   ├── reminders.py       # Reminder schemas
│   │   └── ...                # Other schemas
│   ├── services/              # Business logic & external integrations
│   │   ├── user.py            # User service
│   │   ├── client.py          # Client service
│   │   ├── reminder.py        # Reminder service
│   │   ├── email_service.py   # Email notification service
│   │   ├── sms_service.py     # SMS notification service
│   │   ├── whatsapp_service.py # WhatsApp notification service
│   │   └── scheduler_service.py # APScheduler integration for reminders
│   └── database.py            # Database connection and session management
├── scripts/                   # Utility scripts
└── tests/                     # Test suite
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

### Core Components

- **Settings**: Environment-specific configuration
- **Security**: Authentication, authorization, and encryption
- **Exceptions**: Custom exception types and handling

This architecture provides several benefits:

- **Testability**: Each layer can be tested in isolation
- **Maintainability**: Clear separation of concerns
- **Scalability**: Modular design allows for easier scaling
- **Security**: Centralized security controls and validation

## Deployment Architecture

The Reminder App is designed to be deployed as a centralized service that can manage multiple businesses and their clients. The deployment architecture includes:

- **App Server**: AWS EC2 or ECS for hosting the FastAPI application
- **Database**: AWS RDS MySQL for data persistence
- **Load Balancing**: AWS Application Load Balancer (for scaling)
- **Monitoring**: AWS CloudWatch for logs and metrics
- **Networking**: VPC configuration for security

Each business using the platform (such as accounting firms) will have their own account within the application but will use the same centralized infrastructure.

## User Workflow

1. **Business Setup**: Businesses register and configure their notification preferences
2. **Client Management**: Businesses import or manually add their clients
3. **Reminder Configuration**: Businesses create reminders with specified schedules, messages, and notification channels
4. **Client Assignment**: Clients are associated with specific reminders
5. **Notification Delivery**:
   - Automated delivery based on schedule
   - Manual trigger option for immediate delivery
6. **Client Experience**:
   - Clients receive notifications via preferred channels
   - Clients can view documents/invoices via included links
   - Clients can make payments via Stripe integration
7. **Monitoring**:
   - Businesses track notification history
   - Payment status updates are recorded
   - Error handling for failed notifications or payments

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL database (or SQLite for development/testing)
- AWS account for production deployment
- Twilio account (for SMS)
- SMTP server (for Email)
- WhatsApp Business API access
- Stripe account (for payment processing)

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

Using pip:\

```bash
pip install -r requirements.txt
```

Or using uv (faster):

```bash
uv pip sync requirements.txt
```

#### 4. Configure Environment

```bash
# Create development environment file
cp env/.env.example env/.env.development

# Edit with your development settings
# Set SQLALCHEMY_DATABASE_URI to your database connection
# For quick development: SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db
```

#### 5. Run Migrations

```bash
# Set environment
export ENV=development  # Linux/Mac
set ENV=development     # Windows CMD
$env:ENV = "development"  # PowerShell

# Run migrations
alembic upgrade head
```

#### 6. Start the Application

```bash
python main.py
# Or directly with uvicorn:
# uvicorn app.main:app --reload
```

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
# - Stripe API keys
# - Twilio credentials
# - CORS settings
# - SSL configuration
```

#### 2. Build and Deploy with Docker

```bash
# Build the Docker image
docker build -t reminder-backend:latest .

# Run with Docker
docker run -p 8000:8000 --env-file env/.env.production reminder-backend:latest

# Or use docker-compose
docker-compose up -d
```

#### 3. Monitor Logs

```bash
# View container logs
docker logs -f reminder-backend
```

## Environment Configuration

The application uses environment-specific configuration files located in the `env/` directory:

### Environment Types

- **Development** (`ENV=development`): For local development with debugging features enabled
- **Testing** (`ENV=testing`): For automated tests with SQLite and minimal external dependencies
- **Production** (`ENV=production`): For deployed instances with security features and optimizations

### Configuration Files

Each environment has its own configuration file:

- `env/.env.development` - Development environment settings
- `env/.env.testing` - Testing environment settings
- `env/.env.production` - Production environment settings

### Setting Up Environment Files

Create environment files from the example template:

```bash
# Create environment files from example
cp env/.env.example env/.env.development
cp env/.env.example env/.env.testing
cp env/.env.example env/.env.production

# Edit files with appropriate settings for each environment
```

### Key Configuration Settings

Some important environment variables include:

- **Database Connection**: `SQLALCHEMY_DATABASE_URI` or individual DB_* variables
- **Security Keys**: `SECRET_KEY` for JWT tokens (unique per environment)
- **API Configuration**: `API_V1_STR`, `CORS_ORIGINS`, etc.
- **External Services**: Twilio, SMTP, Stripe credentials
- **Scheduler Settings**: `DISABLE_SCHEDULER`, `SCHEDULER_TIMEZONE`
- **Validation Mode**: `STRICT_VALIDATION` (True/False)

### Running with a Specific Environment

```bash
# Set environment before running
export ENV=development  # Linux/Mac
set ENV=development     # Windows CMD
$env:ENV = "development" # Windows PowerShell

# Then run the application
python main.py
```

Or specify directly when running:

```bash
ENV=development python main.py
```

## Scheduler Service

The application includes a robust scheduler service for processing reminders automatically:

### Scheduler Features

- **Automatic Processing**: Checks for due reminders at regular intervals
- **Smart Recurrence**: Handles various recurrence patterns (daily, weekly, monthly)
- **Multi-channel Delivery**: Sends notifications via email, SMS, or WhatsApp
- **Error Handling**: Robust error handling and retry mechanisms

### Configuration Options

The scheduler service can be configured through environment variables:

```bash
# Set timezone for scheduler operations
SCHEDULER_TIMEZONE=UTC

# Completely disable the scheduler (useful for certain testing scenarios)
DISABLE_SCHEDULER=false
```

### Testing Mode Behavior

In testing environments (`ENV=testing`), the scheduler has special behavior:

- **Auto-Detection**: Checks for existing reminders before starting
- **Smart Disable**: Automatically disables itself if no reminders exist
- **Reduced Logging**: Minimizes log output for cleaner test runs
- **Manual Override**: Can be completely disabled via `DISABLE_SCHEDULER=true`

The scheduler implementation detects the testing environment and adjusts its behavior:

```python
# Example from scheduler_service.py
def start(self):
    """Start the scheduler service."""
    logger.info("Starting reminder scheduler service")
    
    # Check if scheduler should be disabled via configuration
    if getattr(settings, "DISABLE_SCHEDULER", False):
        logger.info("Scheduler disabled via DISABLE_SCHEDULER setting")
        return
    
    # In testing environment, only start if there are reminders
    if settings.ENV == "testing":
        db = SessionLocal()
        try:
            reminder_count = db.query(Reminder).count()
            if reminder_count == 0:
                logger.info("No reminders found in testing environment. Scheduler will not start.")
                return
            logger.info(f"Found {reminder_count} reminders in testing environment. Starting scheduler.")
        finally:
            db.close()
            
    # Continue with regular scheduler initialization...
```

This behavior makes testing more efficient by:

- Preventing unnecessary background processing during tests
- Reducing log noise in test output
- Allowing control over scheduler behavior in different test scenarios

### Scheduler Health Checks

You can verify the scheduler is running correctly by:

1. Checking the application logs for "Scheduler service started" message
2. Monitoring the "Processing due reminders" log messages (every minute)
3. Creating a test reminder with a date in the past and verifying it's processed

## Code Architecture Details

### Repository Pattern

The application implements the Repository Pattern to separate data access logic from business logic:

#### Repository Structure

Each model has a corresponding repository class that handles all database operations:

```python
# Example repository method
async def get_reminder_by_id(db: Session, reminder_id: int) -> Optional[Reminder]:
    return db.query(Reminder).filter(Reminder.id == reminder_id).first()
```

This pattern provides several advantages:

- **Abstraction**: Services don't need to know how data is stored or retrieved
- **Testability**: Repositories can be mocked for service testing
- **Maintainability**: Database queries are centralized and reusable

#### Service-Repository Interaction

Services use repositories to interact with the database:

```python
# Example service using repository
async def process_reminder(reminder_id: int):
    with db_session() as db:
        reminder = await reminder_repository.get_reminder_by_id(db, reminder_id)
        if reminder:
            # Process the reminder...
```

#### Key Repository Methods

Common methods implemented across repositories:

- `create_*` - Create new records
- `get_*_by_id` - Retrieve single records
- `get_*_by_*` - Filter based on criteria
- `list_*` - Retrieve collections with filtering/pagination
- `update_*` - Update existing records
- `delete_*` - Remove records

### Service Implementation

The service layer contains business logic and coordinates across multiple repositories:

- **Stateless Services**: All functions are stateless and take explicit dependencies
- **Transaction Management**: Services manage database transactions
- **External Integration**: Services handle external API calls
- **Error Handling**: Centralized error handling and retries
