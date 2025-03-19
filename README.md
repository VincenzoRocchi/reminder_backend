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
reminder_app/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── main.py                    # Application entry point
├── alembic/                   # Database migrations
├── app/                       # Main application package
│   ├── api/                   # API endpoints
│   ├── core/                  # Core functionality
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   └── services/              # External services integration
│       ├── email_service.py   # Email notification service
│       ├── sms_service.py     # SMS notification service
│       ├── whatsapp_service.py # WhatsApp notification service
│       └── scheduler_service.py # APScheduler integration for reminders
├── scripts/                   # Utility scripts
└── tests/                     # Test suite
```

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
- MySQL database (or Docker for local development)
- AWS account for production deployment
- Twilio account (for SMS)
- SMTP server (for Email)
- WhatsApp Business API access
- Stripe account (for payment processing)

### Installation

#### Option 1: Using uv (Recommended)

uv is a fast Python package installer and resolver that can significantly speed up dependency installation.

1. Install uv (if not already installed) [following these instructions](https://docs.astral.sh/uv/getting-started/installation):

   ```bash
   winget install --id=astral-sh.uv  -e
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/reminder-app.git
   cd reminder-app
   ```

3. Create and activate a virtual environment with uv:

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   uv pip sync [requirements.txt]
   ```

5. Copy `.env.example` to `.env` and configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Run database migrations:

   ```bash
   alembic upgrade head
   ```

#### Option 2: Using pip

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/reminder-app.git
   cd reminder-app
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:

   ```bash
   alembic upgrade head
   ```

### Running the Application

#### Development Mode

```bash
python main.py
```

or

```bash
uvicorn app.main:app --reload
```

#### Using Docker

```bash
docker-compose up
```

### API Documentation

Once the application is running, access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:

``` bash
pytest
```

## Database Migrations

Create a new migration:

``` bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

``` bash
alembic upgrade head
```

## Validation Settings

The application supports two validation modes:

- **Strict Validation** (default in production): All input validation rules are enforced
- **Relaxed Validation** (optional in development): Validation warnings are logged but don't block operations

To enable relaxed validation in development:

```bash
# In your .env.development file
STRICT_VALIDATION=False
```
## License

[MIT](LICENSE)
