# claude-flowchart-mixandmatch Flowchart

```mermaid
flowchart TD
    subgraph NotificationQueues["Notification Queues"]
        EmailQ["Email Queue"] 
        SMSQ["SMS Queue"]
        WhatsAppQ["WhatsApp Queue"]
    end

    subgraph NotificationProcessors["Notification Processors"]
        EP["Email Processor"] --> ET["Template Rendering<br>(Jinja2)"]
        ET --> EA["Attachment Handling"]
        EA --> ES["SMTP Sender"]
        
        SP["SMS Processor"] --> ST["SMS Template<br>Rendering"]
        ST --> TwilioAPI["Twilio API<br>Integration"]
        
        WP["WhatsApp Processor"] --> WT["WhatsApp Template<br>Rendering"]
        WT --> MediaH["Media Handling<br>(if applicable)"]
        MediaH --> WAPI["WhatsApp Business<br>API Integration"]
    end

    subgraph ExternalServices["External Services"]
        ES --> EmailServer["SMTP Server<br>(AWS SES/SendGrid/etc)"]
        TwilioAPI --> Twilio["Twilio API<br>(SMS Gateway)"]
        WAPI --> WhatsAppBusiness["WhatsApp Business<br>API"]
    end

    subgraph DeliveryTracking["Delivery Tracking"]
        Webhook["Webhooks for<br>Status Updates"] --> StatusProc["Status Processor"]
        PollingService["Status Polling<br>Service"] --> StatusProc
        
        StatusProc --> DeliveryStatus[(Delivery Status<br>Database)]
        DeliveryStatus --> Analytics["Analytics & Reporting"]
    end

    subgraph RetryMechanism["Retry Mechanism"]
        FailureHandler["Failure Handler"] --> RetryPolicy["Retry Policy:<br>- Backoff strategy<br>- Max attempts<br>- Timeout"]
        RetryPolicy --> RequeueJob["Requeue Job"]
        RetryPolicy --> FailureLog["Permanent Failure<br>Logger"]
        
        RequeueJob -.-> NotificationQueues
        FailureLog --> AlertSystem["Alert System<br>(for critical failures)"]
    end

    subgraph RateLimiting["Rate Limiting"]
        RateLimiter["API Rate Limiter"] --> Quotas["Service Quotas<br>by Business"]
        RateLimiter --> Throttling["Throttling Logic"]
        RateLimiter --> CostMgmt["Cost Management"]
    end
    
    subgraph ContentValidation["Content Validation"]
        ContentValidator["Content Validator"] --> Templates["Template Validation"]
        ContentValidator --> SizeCheck["Size/Length Check"]
        ContentValidator --> TypeCheck["Content Type Check"]
        ContentValidator --> SanitizeCheck["Content Sanitization"]
    end

    EmailQ --> EP
    SMSQ --> SP
    WhatsAppQ --> WP
    
    EmailServer & Twilio & WhatsAppBusiness --> Webhook
    EmailServer & Twilio & WhatsAppBusiness --> PollingService
    
    ES & TwilioAPI & WAPI --> RateLimiter
    ES & TwilioAPI & WAPI -.-> FailureHandler
    
    NotificationQueues --> ContentValidator
