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
from app.services.twilio_service import TwilioService
from app.models.emailConfigurations import EmailConfiguration
from app.models.senderIdentities import SenderIdentity
from app.models.clients import Client
from app.models.reminderRecipient import ReminderRecipient
from app.core.exceptions import ServiceError
from app.core.settings import settings
from app.services.notification import notification_service

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
        
        The scheduler will not start if DISABLE_SCHEDULER setting is True.
        """
        from app.core.settings import settings
        
        logger.info("Starting reminder scheduler service")
        
        # Check if scheduler should be disabled via configuration
        if getattr(settings, "DISABLE_SCHEDULER", False):
            logger.info("Scheduler disabled via DISABLE_SCHEDULER setting")
            return
        
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
        
        This method:
        1. Finds all reminders that are due and active
        2. For each reminder, ensures notification records exist for all recipients
        3. Processes and sends each notification
        4. Updates reminder and notification statuses
        5. Handles recurring reminders
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
            
            logger.info(f"Found {len(due_reminders)} due reminders to process")
            
            for reminder in due_reminders:
                # Get the user who created the reminder
                user = db.query(User).filter(User.id == reminder.user_id).first()
                if not user or not user.is_active:
                    logger.warning(f"Skipping reminder {reminder.id}: User {reminder.user_id} not found or inactive")
                    continue
                
                try:
                    # Generate notifications for this reminder
                    # This ensures that we have a notification record for each client
                    notifications = notification_service.generate_notifications_for_reminder(
                        db,
                        reminder_id=reminder.id,
                        user_id=reminder.user_id
                    )
                    
                    if not notifications:
                        logger.warning(f"No notifications generated for reminder {reminder.id}: No active clients found")
                        continue
                        
                    logger.info(f"Generated {len(notifications)} notifications for reminder {reminder.id}")
                    
                    # Process the reminder notifications
                    await notification_service.create_and_send_notifications_for_reminder(
                        db, 
                        reminder=reminder
                    )
                    
                    # Handle recurring reminders
                    if reminder.is_recurring and reminder.recurrence_pattern:
                        next_date = self.calculate_next_reminder_date(
                            reminder.reminder_date, reminder.recurrence_pattern
                        )
                        if next_date:
                            reminder.reminder_date = next_date
                            db.add(reminder)
                            db.commit()
                            logger.info(f"Updated recurring reminder {reminder.id} with next date: {next_date}")
                        else:
                            logger.warning(f"Could not calculate next date for recurring reminder {reminder.id}")
                            
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder.id}: {str(e)}", exc_info=True)
                    continue
                        
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
            if notification_type == NotificationTypeEnum.EMAIL:
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
                
            elif notification_type == NotificationTypeEnum.SMS:
                # Determine which phone number to use for recipient
                recipient_phone = None
                if hasattr(client, 'preferred_contact_method') and client.preferred_contact_method == "SMS" and hasattr(client, 'secondary_phone_number') and client.secondary_phone_number:
                    recipient_phone = client.secondary_phone_number
                else:
                    recipient_phone = client.phone_number
                    
                if not recipient_phone:
                    logger.warning(f"Cannot send SMS notification: Missing phone number for client {client.id}")
                    return False
                
                # Determine which phone number to use for sender (from number)
                from_phone_number = None
                
                # First check if we have a sender identity with a PHONE type
                if sender_identity and hasattr(sender_identity, 'identity_type') and sender_identity.identity_type == "PHONE":
                    from_phone_number = sender_identity.value
                    logger.info(f"Using sender identity phone {from_phone_number} for SMS")
                # Fallback to user's phone number
                elif hasattr(user, 'phone_number') and user.phone_number:
                    from_phone_number = user.phone_number
                    logger.info(f"Using user's phone number for SMS")
                
                if not from_phone_number:
                    logger.error(f"Cannot send SMS notification: No sender phone number available")
                    return False
                
                # Use the TwilioService to send SMS
                return TwilioService.send_reminder_message(
                    user=user,
                    recipient_phone=recipient_phone,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                    from_phone_number=from_phone_number,
                    sender_identity=sender_identity,
                    channel="sms"
                )
                
            elif notification_type == NotificationTypeEnum.WHATSAPP:
                # Determine which phone number to use for recipient
                recipient_phone = None
                if hasattr(client, 'preferred_contact_method') and client.preferred_contact_method == "WHATSAPP":
                    if hasattr(client, 'whatsapp_phone_number') and client.whatsapp_phone_number:
                        recipient_phone = client.whatsapp_phone_number
                    elif hasattr(client, 'secondary_phone_number') and client.secondary_phone_number:
                        recipient_phone = client.secondary_phone_number
                    else:
                        recipient_phone = client.phone_number
                else:
                    recipient_phone = client.phone_number
                    
                if not recipient_phone:
                    logger.warning(f"Cannot send WhatsApp notification: Missing phone number for client {client.id}")
                    return False
                
                # Determine which phone number to use for sender (from number)
                from_phone_number = None
                
                # First check if we have a sender identity with a PHONE type
                if sender_identity and hasattr(sender_identity, 'identity_type') and sender_identity.identity_type == "PHONE":
                    from_phone_number = sender_identity.value
                    logger.info(f"Using sender identity phone {from_phone_number} for WhatsApp")
                # Fallback to user's phone number
                elif hasattr(user, 'phone_number') and user.phone_number:
                    from_phone_number = user.phone_number
                    logger.info(f"Using user's phone number for WhatsApp")
                
                if not from_phone_number:
                    logger.error(f"Cannot send WhatsApp notification: No sender phone number available")
                    return False
                
                # Use the TwilioService to send WhatsApp
                return TwilioService.send_reminder_message(
                    user=user,
                    recipient_phone=recipient_phone,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                    from_phone_number=from_phone_number,
                    sender_identity=sender_identity,
                    channel="whatsapp"
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