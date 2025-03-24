import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import SessionLocal
from app.models.reminders import Reminder, NotificationType
from app.models.notifications import Notification, ReminderStatus
from app.models.users import User
from app.models.business import Business
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.whatsapp_service import WhatsAppService
from app.models.serviceAccounts import ServiceAccount
from app.models.clients import Client
from app.models.reminderRecipient import ReminderRecipient

# Configure module-level logger for this service
# This allows targeted log filtering and appropriate log levels
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for scheduling and processing reminders.
    
    This service manages the scheduled execution of reminder notifications
    for businesses to their users. It handles:
    - Periodic checking of due reminders
    - Sending notifications through multiple channels (email, SMS, WhatsApp)
    - Managing recurring reminders with various patterns
    - Updating reminder and notification statuses
    
    Design Decisions:
    - Uses AsyncIOScheduler for non-blocking, efficient reminder processing
    - Implements a singleton pattern to ensure only one scheduler is running
    - Separates notification sending logic by channel type for maintainability
    - Uses SQLAlchemy ORM for database interactions to abstract DB operations
    """
    
    def __init__(self):
        """
        Initialize the scheduler service.
        
        Creates an AsyncIOScheduler instance but does not start it automatically.
        The scheduler must be explicitly started using the start() method.
        """
        # Using AsyncIOScheduler for compatibility with asyncio-based applications
        # This allows for non-blocking reminder processing
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """
        Start the scheduler service.
        
        Registers the process_reminders job to run at 1-minute intervals
        and activates the scheduler. This job frequency represents a balance
        between timely reminder delivery and system load.
        """
        logger.info("Starting reminder scheduler service")
        
        # Add job to process reminders every minute
        # IntervalTrigger ensures reliable execution at fixed intervals
        # ID allows for job identification and replacement if needed
        self.scheduler.add_job(
            self.process_reminders,
            IntervalTrigger(minutes=1),
            id="process_reminders",
            replace_existing=True,  # Prevents duplicate jobs if restarted
        )
        
        # Start the scheduler - after this point, jobs will begin executing
        self.scheduler.start()
    
    async def process_reminders(self):
        """
        Process reminders that are due to be sent.
        """
        logger.info("Processing due reminders")
        
        db = SessionLocal()
        try:
            now = datetime.now()
            
            # Find reminders that are due and active
            due_reminders = (
                db.query(Reminder)
                .filter(
                    Reminder.reminder_date <= now,
                    Reminder.is_active == True
                )
                .all()
            )
            
            for reminder in due_reminders:
                # Get the user who created the reminder
                user = db.query(User).filter(User.id == reminder.user_id).first()
                if not user or not user.is_active:
                    continue
                    
                # Get the service account for this reminder
                service_account = None
                if reminder.service_account_id:
                    service_account = db.query(ServiceAccount).filter(
                        ServiceAccount.id == reminder.service_account_id,
                        ServiceAccount.is_active == True
                    ).first()
                
                # If no specific service account is provided, try to find a default one
                if not service_account:
                    service_account = db.query(ServiceAccount).filter(
                        ServiceAccount.user_id == user.id,
                        ServiceAccount.service_type == reminder.notification_type,
                        ServiceAccount.is_active == True
                    ).first()
                    
                # Skip if no valid service account is found
                if not service_account:
                    logger.warning(f"No active service account found for reminder {reminder.id} with type {reminder.notification_type}")
                    continue
                
                # Get all clients for this reminder
                recipient_mappings = (
                    db.query(ReminderRecipient)
                    .filter(ReminderRecipient.reminder_id == reminder.id)
                    .all()
                )
                
                client_ids = [mapping.client_id for mapping in recipient_mappings]
                clients = db.query(Client).filter(Client.id.in_(client_ids), Client.is_active == True).all()
                
                # Process each client
                for client in clients:
                    # Check if a notification already exists
                    existing_notification = (
                        db.query(Notification)
                        .filter(
                            Notification.reminder_id == reminder.id,
                            Notification.client_id == client.id,
                            Notification.status.in_([ReminderStatus.PENDING, ReminderStatus.SENT])
                        )
                        .first()
                    )
                    
                    # Skip if already processed
                    if existing_notification and existing_notification.status == ReminderStatus.SENT:
                        continue
                    
                    # Create a new notification if one doesn't exist
                    if not existing_notification:
                        notification = Notification(
                            reminder_id=reminder.id,
                            client_id=client.id,
                            notification_type=reminder.notification_type,
                            message=reminder.description,
                            status=ReminderStatus.PENDING
                        )
                        db.add(notification)
                        db.commit()
                        db.refresh(notification)
                    else:
                        notification = existing_notification
                    
                    # Send the notification
                    success = await self.send_notification(
                        notification_type=reminder.notification_type,
                        service_account=service_account,
                        user=user,
                        client=client,
                        reminder=reminder
                    )
                    
                    # Update notification status
                    notification.sent_at = datetime.now()
                    if success:
                        notification.status = ReminderStatus.SENT
                    else:
                        notification.status = ReminderStatus.FAILED
                        notification.error_message = "Failed to send notification"
                    
                    db.add(notification)
                
                # Handle recurring reminders
                if reminder.is_recurring and reminder.recurrence_pattern:
                    next_date = self.calculate_next_reminder_date(
                        reminder.reminder_date, reminder.recurrence_pattern
                    )
                    if next_date:
                        reminder.reminder_date = next_date
                    else:
                        reminder.is_active = False
                else:
                    reminder.is_active = False
                
                db.add(reminder)
                
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing reminders: {str(e)}", exc_info=True)
        finally:
            db.close()
            
    async def send_notification(
        self,
        notification_type: NotificationType,
        service_account,
        user,
        client,
        reminder,
    ) -> bool:
        """
        Send a notification based on its configured type.
        """
        try:
            if notification_type == NotificationType.EMAIL:
                if not client.email:
                    logger.warning(f"Cannot send email notification: Missing email for client {client.id}")
                    return False
                
                return await EmailService.send_reminder_email(
                    service_account=service_account,
                    user=user,
                    recipient_email=client.email,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description or "",
                )
                
            elif notification_type == NotificationType.SMS:
                if not client.phone_number:
                    logger.warning(f"Cannot send SMS notification: Missing phone number for client {client.id}")
                    return False
                
                return SMSService.send_reminder_sms(
                    service_account=service_account,
                    user=user,
                    recipient_phone=client.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
                
            elif notification_type == NotificationType.WHATSAPP:
                if not client.phone_number:
                    logger.warning(f"Cannot send WhatsApp notification: Missing phone number for client {client.id}")
                    return False
                
                return await WhatsAppService.send_reminder_whatsapp(
                    service_account=service_account,
                    user=user,
                    recipient_phone=client.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
            
            logger.error(f"Unsupported notification type: {notification_type}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending {notification_type} notification: {str(e)}", exc_info=True)
            return False
        
    def calculate_next_reminder_date(self, current_date: datetime, pattern: str) -> datetime:
        """
        Calculate the next reminder date based on the recurrence pattern.
        
        Supports various recurrence patterns including:
        - Simple periods: daily, weekly, monthly, yearly
        - Complex patterns: "every X days/weeks/months"
        
        Important business logic for recurring reminders, handling the
        scheduling complexity for different time periods.
        
        Args:
            current_date: Base date to calculate from
            pattern: Text description of recurrence (e.g., 'daily', 'weekly', 'every 2 weeks')
            
        Returns:
            Next reminder date or None if pattern is invalid
        """
        try:
            # Normalize pattern for case-insensitive matching
            pattern = pattern.lower()
            
            # Handle simple recurring patterns
            if pattern == 'daily':
                return current_date + timedelta(days=1)
            
            elif pattern == 'weekly':
                return current_date + timedelta(weeks=1)
            
            elif pattern == 'monthly':
                # Monthly calculation requires special handling for different month lengths
                # This implementation handles month boundaries correctly
                new_month = current_date.month + 1
                new_year = current_date.year
                
                # Handle year rollover if needed
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                
                # Handle month length differences
                # Using 28 as a safe default to prevent invalid dates
                # For more sophisticated handling, consider calendar libraries
                day = min(current_date.day, 28)  # Simple handling for month lengths
                
                return current_date.replace(year=new_year, month=new_month, day=day)
            
            elif pattern == 'yearly':
                # Simple yearly recurrence - same month/day, next year
                return current_date.replace(year=current_date.year + 1)
            
            # Handle complex patterns with a quantity and unit
            # Format: "every X days/weeks/months"
            elif pattern.startswith('every '):
                # Split into components: ["every", "X", "days"]
                parts = pattern.split()
                if len(parts) >= 3:
                    try:
                        # Extract the numerical multiplier
                        number = int(parts[1])
                        # Extract the time unit (singular or plural)
                        unit = parts[2].lower()
                        
                        # Apply multiplier based on time unit
                        if unit in ('day', 'days'):
                            return current_date + timedelta(days=number)
                        elif unit in ('week', 'weeks'):
                            return current_date + timedelta(weeks=number)
                        elif unit in ('month', 'months'):
                            # Calculate multi-month increments
                            # This handles year boundaries automatically
                            new_month = current_date.month + number
                            new_year = current_date.year
                            
                            # Handle year rollovers for multi-month increments
                            while new_month > 12:
                                new_month -= 12
                                new_year += 1
                            
                            # Handle month length differences
                            day = min(current_date.day, 28)
                            
                            return current_date.replace(year=new_year, month=new_month, day=day)
                    except ValueError:
                        # Handle non-numeric values in the pattern
                        logger.warning(f"Invalid numeric value in pattern: {pattern}")
                        pass
            
            # If pattern format is not recognized
            logger.warning(f"Unrecognized recurrence pattern: {pattern}")
            return None
            
        except Exception as e:
            # Log detailed error for debugging
            # This helps identify issues with specific recurrence patterns
            logger.error(f"Error calculating next reminder date: {str(e)}", exc_info=True)
            return None
        
    def __str__(self):
        """
        Provides a human-readable string representation of the scheduler service.
        
        Returns:
            String with service status and job count for logging and debugging
        """
        status = "running" if hasattr(self, 'scheduler') and getattr(self.scheduler, 'running', False) else "stopped"
        job_count = len(self.scheduler.get_jobs()) if hasattr(self, 'scheduler') else 0
        return f"Reminder Scheduler Service ({status}, {job_count} jobs)"

    def __repr__(self):
        """
        Provides a detailed technical representation of the scheduler service.
        
        Used for debugging and development to quickly assess service state.
        
        Returns:
            String with the object's technical representation including status
        """
        if hasattr(self, 'scheduler'):
            status = 'running' if getattr(self.scheduler, 'running', False) else 'stopped'
            job_count = len(self.scheduler.get_jobs())
        else:
            status = 'uninitialized'
            job_count = 0
        return f"<SchedulerService status={status} jobs={job_count}>"


# Create a singleton instance
# This ensures only one scheduler is running application-wide
# All imports of this module will use the same scheduler instance
scheduler_service = SchedulerService()