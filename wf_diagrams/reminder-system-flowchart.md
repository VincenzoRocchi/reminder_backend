# reminder-system-flowchart Flowchart

```mermaid
flowchart TD
    subgraph BusinessUI["Business Admin Interface"]
        Create["Create Reminder"] --> RType["Select Reminder Type:<br>- Payment<br>- Deadline<br>- Notification"]
        Create --> RSchedule["Set Schedule:<br>- One-time<br>- Recurring<br>- Rule-based"]
        Create --> RContent["Define Content:<br>- Message Template<br>- Variables<br>- Attachments/Links"]
        Create --> RChannels["Select Channels:<br>- Email<br>- SMS<br>- WhatsApp"]
        Create --> RClients["Assign Recipients:<br>- Individual clients<br>- Client groups<br>- All clients"]
        ManualTrig["Manual Trigger"] --> SpecificR["Select Specific Reminder"]
        ManualTrig --> SpecificC["Select Specific Clients"]
    end

    subgraph APILayer["Reminder API Layer"]
        ReminderCRUD["Reminder CRUD<br>Endpoints"] --> Validation["Request Validation<br>(Pydantic)"]
        Validation --> BusinessCheck["Business Access<br>Verification"]
        BusinessCheck --> DataOps["Database Operations"]
        
        ManualTrigger["Manual Trigger<br>Endpoint"] --> TriggerValidation["Trigger Validation"]
        TriggerValidation --> TriggerExec["Execute Trigger"]
    end

    subgraph DataLayer["Data Persistence"]
        DataOps --> RemindersDB[(Reminders Table)]
        DataOps --> ClientsDB[(Clients Table)]
        DataOps --> TemplatesDB[(Message Templates)]
        DataOps --> RulesDB[(Reminder Rules)]
        RemindersDB --> RecipientMap[(Reminder-Client<br>Mapping)]
    end

    subgraph SchedulerSystem["Scheduler System"]
        APSched["APScheduler"] --> JobStore["Job Store<br>(Database)"]
        APSched --> Executors["Thread/Process<br>Executors"]
        
        JobTypes["Job Types"] --> Recurring["Recurring Jobs<br>(using cron syntax)"]
        JobTypes --> OneTime["One-time Jobs<br>(using exact datetime)"]
        JobTypes --> Dynamic["Dynamic Jobs<br>(calculated at runtime)"]
        
        TriggerExec --> APSched
        
        APSched --> JobExec["Job Execution"]
    end

    subgraph ProcessingPipeline["Reminder Processing Pipeline"]
        JobExec --> LoadReminder["Load Reminder<br>Details"]
        LoadReminder --> FetchRecipients["Fetch Recipients"]
        FetchRecipients --> ProcessTemplate["Process Template<br>with Variables"]
        ProcessTemplate --> GenerateContent["Generate Notification<br>Content"]
        GenerateContent --> PrepareDelivery["Prepare for Delivery<br>(by channel)"]
        PrepareDelivery --> QueueNotifications["Queue Notifications<br>for Delivery"]
        QueueNotifications --> TrackStatus["Track Processing<br>Status"]
    end

    subgraph NotificationQueue["Notification Queue"]
        QueueSystem["Queue System<br>(RabbitMQ/Redis)"] --> QWorkers["Queue Workers"]
        QWorkers --> NotificationSystem["Notification<br>System"]
        QWorkers --> HistoryLog["History Logger"]
    end

    BusinessUI --> APILayer
    ProcessingPipeline --> NotificationQueue
    DataLayer --> LoadReminder
