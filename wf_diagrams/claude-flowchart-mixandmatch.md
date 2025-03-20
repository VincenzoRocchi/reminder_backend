# claude-flowchart-mixandmatch Flowchart

```mermaid
flowchart TD

    subgraph Core["Core System (FastAPI Backend)"]
        API["API Endpoints"] --> Auth["Authentication (JWT)"]
        API --> RM["Reminder Management"]
        API --> BM["Business Management"]
        API --> UM["User Management"]
        SCH["Scheduler Service (APScheduler)"] --> NT["Notification Triggers"]
    end

    subgraph Businesses["Business Accounts"]
        BA["Business Admin"] --> BC["Create/Modify Business Settings"]
        BA --> RP["Reminder Configuration"] 
        BA --> CP["Client Management"]
        RP --> RD["Define Reminders:<br>- Type (deadline, payment)<br>- Schedule (date/recurrence)<br>- Message content<br>- Notification channels<br>- Payment links (Stripe)"]
        CP --> CC["Assign Clients to Reminders"]
        BA --> MT["Manual Trigger"]
        BA --> DS["Dashboard & Analytics"]
    end

    subgraph Notifications["Notification System"]
        NT --> ES["Email Service<br>(SMTP)"]
        NT --> SS["SMS Service<br>(Twilio)"]
        NT --> WS["WhatsApp Service<br>(WhatsApp Business API)"]
        ES & SS & WS --> NH["Notification History"]
        ES & SS & WS -.-> EH["Error Handling"]
    end

    subgraph Clients["Client Experience"]
        CU["Client Users"] --> RN["Receive Notifications"]
        RN --> VD["View Documents/Invoices"]
        RN --> PP["Process Payments<br>(Stripe Integration)"]
        PP --> PS["Payment Status Update"]
    end

    subgraph Data["Data Layer"]
        DB[(AWS RDS MySQL)] --- ORM["SQLAlchemy ORM"]
        ORM --- MIG["Alembic Migrations"]
    end

    Core --- Businesses
    SCH --> RCJ["Run scheduled checks<br>for pending reminders"]
    RCJ --> NT
    MT --> NT
    Notifications --- Clients
    Core --- Data
    PS --> NH
