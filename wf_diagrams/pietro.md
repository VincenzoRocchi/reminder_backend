# pietro Flowchart

```mermaid
flowchart TD
    A["Admin (Accounting firm)"] --> B{"Create/Modify Reminder"} & C{"Automatic system (Cron Job)"} & D["End client"]
    B --> B1["Defines: <br>Type (deadline, payment), <br>Month date, <br>Message, <br>Channel (WhatsApp/Email), <br>Invoice/Payment Link"] & B2["Associates Clients <br>(pre-imported or manually added)"]
    C --> C1["Every day checks reminders with date = current day"] & C15["Possibility of manual trigger (early sending)"]
    C1 --> C11{"For each expired or expiring reminder"}
    C11 --> C12["Generates notification for each associated client"]
    C12 --> C121["Email<br>Sends message with invoice/payment link (Stripe)"] & C122["WhatsApp<br>Sends message with invoice/payment link (Stripe)"]
    C12 -.-> n1(("ERROR HANDLING<br>(Notification Sending Error)"))
    D --> D1["Receives notification (Email/WhatsApp)"] & D2["History of notifications/payments visible in admin portal"]
    D1 --> D11["Views invoice (attached link)"] & D12["Makes payment (Stripe link)"]
    C122 --> C13["Records history of sent notifications"]
    C122 -.-> n2["ERROR HANDLING<br>(Payment Error)"]
    C121 -.-> n2
    C13 --> C14["Updates reminder status <br>(executed)"]
    C121 --> C13
