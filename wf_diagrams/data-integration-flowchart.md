# data-integration-flowchart Flowchart

```mermaid
flowchart TD
    subgraph DatabaseInfrastructure["Database Infrastructure"]
        PrimaryDB[(AWS RDS MySQL<br>Primary Database)] <--> ReadReplica[(Read Replicas<br>for Scaling)]
        
        subgraph DatabaseModels["Key Database Models"]
            Users[("Users<br>(Authentication)")]
            Businesses[("Businesses<br>(Multi-tenancy)")]
            Clients[("Clients<br>(Recipients)")]
            Reminders[("Reminders<br>(Core entity)")]
            Templates[("Message Templates")]
            Notifications[("Notification History")]
            Payments[("Payment Records")]
            AuditLogs[("Audit Logs")]
            
            Users --> Businesses
            Businesses --> Clients
            Businesses --> Reminders
            Businesses --> Templates
            Reminders --> Notifications
            Notifications --> Payments
            Users & Businesses & Reminders --> AuditLogs
        end
        
        DBMigrations["Database Migrations<br>(Alembic)"] --> SchemaVersion["Schema Versioning"]
        DBMigrations --> PrimaryDB
    end
    
    subgraph APILayer["API Integration Layer"]
        CoreAPI["Core API<br>(FastAPI)"] --> Authentication["Authentication<br>Endpoints"]
        CoreAPI --> BusinessAPI["Business<br>Endpoints"]
        CoreAPI --> ClientAPI["Client<br>Endpoints"]
        CoreAPI --> ReminderAPI["Reminder<br>Endpoints"]
        CoreAPI --> NotificationAPI["Notification<br>Endpoints"]
        CoreAPI --> PaymentAPI["Payment<br>Endpoints"]
        CoreAPI --> WebhookAPI["Webhook<br>Endpoints"]
        
        subgraph MiddlewareStack["Middleware Stack"]
            AuthMiddleware["Authentication<br>Middleware"]
            TenantMiddleware["Tenant Isolation<br>Middleware"]
            RateLimitMiddleware["Rate Limiting<br>Middleware"]
            LoggingMiddleware["Logging<br>Middleware"]
            ErrorHandlingMiddleware["Error Handling<br>Middleware"]
        end
        
        CoreAPI --> MiddlewareStack
    end
    
    subgraph ExternalIntegrations["External Service Integrations"]
        subgraph NotificationProviders["Notification Providers"]
            EmailSvc["Email Service<br>(SMTP/AWS SES)"]
            SMSSvc["SMS Service<br>(Twilio)"]
            WhatsAppSvc["WhatsApp Business<br>API"]
        end
        
        subgraph PaymentProviders["Payment Providers"]
            StripeService["Stripe API"]
            PayPalService["PayPal API<br>(Optional)"]
        end
        
        subgraph BusinessIntegrations["Business Integrations"]
            CRMIntegration["CRM Systems<br>(Optional)"]
            AccountingIntegration["Accounting Software<br>(Optional)"]
            CalendarIntegration["Calendar Systems<br>(Optional)"]
        end
        
        subgraph FilestorageSystems["File Storage Systems"]
            S3Storage["AWS S3<br>(Attachments)"]
            CDNService["Content Delivery<br>Network"]
        end
    end
    
    subgraph BackgroundProcessing["Background Processing"]
        TaskQueue["Task Queue<br>(Redis/RabbitMQ)"] --> Workers["Worker Processes"]
        Workers --> ScheduledTasks["Scheduled Tasks"]
        Workers --> NotificationWorkers["Notification<br>Processing"]
        Workers --> ReportGenerators["Report Generation"]
        Workers --> DataExporters["Data Export"]
    end
    
    subgraph MonitoringSystem["Monitoring & Logging"]
        APMTool["Application Performance<br>Monitoring (APM)"] --> PerformanceMetrics["Performance Metrics"]
        LogAggregator["Log Aggregation<br>(CloudWatch)"] --> LogStorage["Log Storage"]
        
        ErrorTracker["Error Tracking<br>Service"] --> AlertSystem["Alert System"]
        
        UsageAnalytics["Usage Analytics"] --> BusinessMetrics["Business Metrics"]
        UsageAnalytics --> SystemMetrics["System Metrics"]
    end
    
    subgraph DeploymentInfrastructure["Deployment Infrastructure"]
        DockerContainers["Docker Containers"] --> AppServers["Application<br>Servers (EC2/ECS)"]
        LoadBalancer["AWS Application<br>Load Balancer"] --> AppServers
        
        CICD["CI/CD Pipeline"] --> DockerBuild["Docker Image<br>Building"]
        DockerBuild --> ImageRegistry["Container Registry"]
        ImageRegistry --> DockerContainers
    end
    
    APILayer <--> DatabaseInfrastructure
    APILayer <--> ExternalIntegrations
    APILayer <--> BackgroundProcessing
    APILayer -.-> MonitoringSystem
    DeploymentInfrastructure -.-> MonitoringSystem
    BackgroundProcessing -.-> MonitoringSystem
