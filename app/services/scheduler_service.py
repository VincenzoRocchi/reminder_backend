# app/services/scheduler_service.py
import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import SessionLocal
from app.models.reminders import Reminder, NotificationTypeEnum
from app.models.notifications import Notification, NotificationStatusEnum
from app.models.users import User
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.whatsapp_service import WhatsAppService
from app.models.emailConfigurations import EmailConfiguration
from app.models.senderIdentities import SenderIdentity
from app.models.clients import Client
from app.models.reminderRecipient import ReminderRecipient
from app.core.exceptions import ServiceError

# Configure module-level logger for this service
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
    """
    
    def __init__(self):
        """
        Initialize the scheduler service.
        
        Creates an AsyncIOScheduler instance but does not start it automatically.
        The scheduler must be explicitly started using the start() method.
        """
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
                    logger.warning(f"Skipping reminder {reminder.id}: User {reminder.user_id} not found or inactive")
                    continue
                
                # For email reminders, ensure we have a valid email configuration
                email_configuration = None
                if reminder.notification_type == NotificationType.EMAIL:
                    if reminder.email_configuration_id:
                        email_configuration = db.query(EmailConfiguration).filter(
                            EmailConfiguration.id == reminder.email_configuration_id,
                            EmailConfiguration.user_id == user.id,
                            EmailConfiguration.is_active == True
                        ).first()
                    
                    if not email_configuration:
                        logger.warning(f"Skipping reminder {reminder.id}: No active email configuration found")
                        continue
                
                # Get sender identity if specified
                sender_identity = None
                if reminder.sender_identity_id:
                    sender_identity = db.query(SenderIdentity).filter(
                        SenderIdentity.id == reminder.sender_identity_id,
                        SenderIdentity.user_id == user.id
                    ).first()
                    
                    if not sender_identity:
                        logger.warning(f"Reminder {reminder.id} specified sender_identity_id {reminder.sender_identity_id} which was not found")
                
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
                            Notification.status.in_([NotificationStatusEnum.PENDING, NotificationStatusEnum.SENT])
                        )
                        .first()
                    )
                    
                    # Skip if already processed
                    if existing_notification and existing_notification.status == NotificationStatusEnum.SENT:
                        continue
                    
                    # Create a new notification if one doesn't exist
                    if not existing_notification:
                        notification = Notification(
                            reminder_id=reminder.id,
                            client_id=client.id,
                            notification_type=reminder.notification_type,
                            message=reminder.description,
                            status=NotificationStatusEnum.PENDING
                        )
                        db.add(notification)
                        db.commit()
                        db.refresh(notification)
                    else:
                        notification = existing_notification
                    
                    # Send the notification
                    success = await self.send_notification(
                        notification_type=reminder.notification_type,
                        email_configuration=email_configuration,  # Only used for email
                        sender_identity=sender_identity,
                        user=user,
                        client=client,
                        reminder=reminder
                    )
                    
                    # Update notification status
                    notification.sent_at = datetime.now()
                    if success:
                        notification.status = NotificationStatusEnum.SENT
                    else:
                        notification.status = NotificationStatusEnum.FAILED
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
        notification_type: NotificationTypeEnum,
        user,
        client,
        reminder,
        email_configuration=None,
        sender_identity=None,
    ) -> bool:
        """
        Send a notification based on the specified type and details.
        
        Args:
            notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
            user: User sending the reminder
            client: Client receiving the reminder
            reminder: Reminder details
            email_configuration: Configuration for sending emails (only used for EMAIL type)
            sender_identity: Optional identity information for display to recipient
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            if notification_type == NotificationType.EMAIL:
                # For email, we use email configurations
                if not client.email:
                    logger.warning(f"Cannot send email notification: Missing email for client {client.id}")
                    return False
                
                if not email_configuration:
                    logger.warning(f"Cannot send email: No email configuration for reminder {reminder.id}")
                    return False
                
                return await EmailService.send_reminder_email(
                    email_configuration=email_configuration,
                    user=user,
                    recipient_email=client.email,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description or "",
                    sender_identity=sender_identity
                )
                
            elif notification_type == NotificationType.SMS:
                # Determine which phone number to use
                phone_number = None
                if hasattr(client, 'preferred_contact_method') and client.preferred_contact_method == "SMS" and hasattr(client, 'secondary_phone_number') and client.secondary_phone_number:
                    phone_number = client.secondary_phone_number
                else:
                    phone_number = client.phone_number
                    
                if not phone_number:
                    logger.warning(f"Cannot send SMS notification: Missing phone number for client {client.id}")
                    return False
                
                return SMSService.send_reminder_sms(
                    user=user,
                    sender_identity=sender_identity,
                    recipient_phone=phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
                
            elif notification_type == NotificationType.WHATSAPP:
                # Determine which phone number to use
                phone_number = None
                if hasattr(client, 'preferred_contact_method') and client.preferred_contact_method == "WHATSAPP":
                    if hasattr(client, 'whatsapp_phone_number') and client.whatsapp_phone_number:
                        phone_number = client.whatsapp_phone_number
                    elif hasattr(client, 'secondary_phone_number') and client.secondary_phone_number:
                        phone_number = client.secondary_phone_number
                    else:
                        phone_number = client.phone_number
                else:
                    phone_number = client.phone_number
                    
                if not phone_number:
                    logger.warning(f"Cannot send WhatsApp notification: Missing phone number for client {client.id}")
                    return False
                
                return await WhatsAppService.send_reminder_whatsapp(
                    user=user,
                    sender_identity=sender_identity,
                    recipient_phone=phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
            
            logger.error(f"Unsupported notification type: {notification_type}")
            return False
            
        except ServiceError as se:
            logger.error(f"Service error: {se.message}", exc_info=True)
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
                new_month = current_date.month + 1
                new_year = current_date.year
                
                # Handle year rollover if needed
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                
                # Handle month length differences
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
            logger.error(f"Error calculating next reminder date: {str(e)}", exc_info=True)
            return None
        
    def __str__(self):
        """
        Provides a human-readable string representation of the scheduler service.
        """
        status = "running" if hasattr(self, 'scheduler') and getattr(self.scheduler, 'running', False) else "stopped"
        job_count = len(self.scheduler.get_jobs()) if hasattr(self, 'scheduler') else 0
        return f"Reminder Scheduler Service ({status}, {job_count} jobs)"

    def __repr__(self):
        """
        Provides a detailed technical representation of the scheduler service.
        """
        if hasattr(self, 'scheduler'):
            status = 'running' if getattr(self.scheduler, 'running', False) else 'stopped'
            job_count = len(self.scheduler.get_jobs())
        else:
            status = 'uninitialized'
            job_count = 0
        return f"<SchedulerService status={status} jobs={job_count}>"


# Create a singleton instance
scheduler_service = SchedulerService()