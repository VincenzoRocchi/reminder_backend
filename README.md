# Reminder App

A comprehensive backend system for businesses to manage and send reminders to their users via email, SMS, and WhatsApp.

## Features

- **User Management**: Register, authenticate, and manage users
- **Business Management**: Create and manage businesses
- **Reminder System**: Set up one-time or recurring reminders
- **Multi-channel Notifications**: Send reminders via email, SMS, or WhatsApp
- **Scheduling**: Automated reminder delivery at specified times
- **Business-specific Settings**: Each business can configure their own notification channels

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | FastAPI (Python) |
| **Database** | AWS RDS (MySQL) |
| **ORM** | SQLAlchemy |
| **Migrations** | Alembic |
| **Notifications** | SMTP (Email), Twilio (SMS), WhatsApp Business API |
| **Deployment** | Docker + AWS EC2/ECS |
| **Reverse Proxy** | Nginx or AWS ALB |
| **Task Scheduling** | APScheduler |
| **Authentication** | JWT (OAuth2) |
| **API Documentation** | Swagger/OpenAPI |
| **Testing** | Pytest |

## Project Structure

```
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
├── scripts/                   # Utility scripts
└── tests/                     # Test suite
```

## Deployment Architecture

The Reminder App is designed to be deployed as a centralized service that can manage multiple businesses and their users. The deployment architecture includes:

- **App Server**: AWS EC2 or ECS for hosting the FastAPI application
- **Database**: AWS RDS MySQL for data persistence
- **Load Balancing**: AWS Application Load Balancer (for scaling)
- **Monitoring**: AWS CloudWatch for logs and metrics
- **Networking**: VPC configuration for security

Each business using the platform will have their own account within the application but will use the same centralized infrastructure.

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL database (or Docker for local development)
- AWS account for production deployment
- Twilio account (for SMS)
- SMTP server (for Email)
- WhatsApp Business API access

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure environment variables
5. Run database migrations:
   ```
   alembic upgrade head
   ```

### Running the Application

#### Development Mode

```
python main.py
```

or 

```
uvicorn app.main:app --reload
```

#### Using Docker

```
docker-compose up
```

## API Documentation

Once the application is running, access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:

```
pytest
```

## Database Migrations

Create a new migration:

```
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```
alembic upgrade head
```

## License

[MIT](LICENSE)