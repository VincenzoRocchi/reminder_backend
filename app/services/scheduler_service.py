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
from app.core.exceptions import ServiceError, InvalidConfigurationError
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
        
        Returns:
            bool: True if scheduler was started, False if disabled
        """
        from app.core.settings import settings
        
        logger.info("Starting reminder scheduler service")
        
        # Check if scheduler should be disabled via configuration
        if getattr(settings, "DISABLE_SCHEDULER", False):
            logger.info("Scheduler disabled via DISABLE_SCHEDULER setting")
            return False
        
        # Add job to process reminders every minute
        self.scheduler.add_job(
            self.process_reminders,
            IntervalTrigger(minutes=1),
            id="process_reminders",
            replace_existing=True,  # Prevents duplicate jobs if restarted
        )
        
        # Start the scheduler - after this point, jobs will begin executing
        self.scheduler.start()
        logger.info("Scheduler service started successfully")
        return True
    
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
        Send a notification of the specified type.
        
        Args:
            notification_type: Type of notification to send
            user: User object
            client: Client object
            reminder: Reminder object
            email_configuration: Optional email configuration
            sender_identity: Optional sender identity
            
        Returns:
            bool: True if notification sent successfully, False otherwise
            
        Raises:
            ServiceError: If notification sending fails
        """
        try:
            if notification_type == NotificationTypeEnum.EMAIL:
                if not client.email:
                    logger.error(f"Cannot send email notification: Client {client.id} has no email address")
                    raise ServiceError("notification", f"Client {client.id} has no email address")
                
                if not email_configuration:
                    logger.error(f"Cannot send email notification: No email configuration provided")
                    raise ServiceError("notification", "No email configuration provided for email notification")
                
                # Use email_configuration to send the email
                recipient_email = client.email
                subject = f"Reminder: {reminder.title}"
                body = reminder.description or "You have a reminder."
                
                # Generate HTML content for the email
                html_content = f"""
                <html>
                <body>
                    <h1>{reminder.title}</h1>
                    <p>{reminder.description or ""}</p>
                    <p>This is an automated reminder from {user.business_name or user.first_name}.</p>
                </body>
                </html>
                """
                
                # Use the EmailService to send the email
                return await EmailService.send_email(
                    email_configuration=email_configuration,
                    recipient_email=recipient_email,
                    subject=subject,
                    body=body,
                    html_content=html_content
                )
                
            elif notification_type == NotificationTypeEnum.SMS:
                # Check if client has a phone number
                if not client.phone_number:
                    logger.error(f"Cannot send SMS notification: Client {client.id} has no phone number")
                    raise ServiceError("notification", f"Client {client.id} has no phone number")
                
                # Use the TwilioService to send the SMS
                recipient_phone = client.phone_number
                
                # Determine sender phone number
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
                    raise ServiceError("notification", "No sender phone number available for SMS notification")
                
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
                # Check if client has a WhatsApp phone number
                recipient_phone = None
                if client.whatsapp_phone_number:
                    recipient_phone = client.whatsapp_phone_number
                    logger.info(f"Using client's WhatsApp number {recipient_phone}")
                elif client.phone_number:
                    recipient_phone = client.phone_number
                    logger.info(f"Using client's regular phone number {recipient_phone} for WhatsApp")
                
                if not recipient_phone:
                    logger.error(f"Cannot send WhatsApp notification: Client {client.id} has no phone number")
                    raise ServiceError("notification", f"Client {client.id} has no phone number for WhatsApp")
                
                # Determine sender phone number
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
                    raise ServiceError("notification", "No sender phone number available for WhatsApp notification")
                
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
            raise ServiceError("notification", f"Unsupported notification type: {notification_type}")
            
        except ServiceError as se:
            logger.error(f"Service error: {se.message}", exc_info=True)
            raise  # Re-raise service errors
        except Exception as e:
            logger.error(f"Error sending {notification_type} notification: {str(e)}", exc_info=True)
            raise ServiceError("notification", f"Failed to send {notification_type} notification", str(e))
        
    def calculate_next_reminder_date(self, current_date: datetime, pattern: str) -> datetime:
        """
        Calculate the next date a reminder should be sent based on a pattern.
        
        Args:
            current_date: The current date to calculate from
            pattern: The recurrence pattern (DAILY, WEEKLY_MON, MONTHLY_1, etc.)
            
        Returns:
            datetime: The next date the reminder should be sent
            
        Raises:
            InvalidConfigurationError: If the pattern is invalid or unsupported
        """
        try:
            if not pattern or pattern == "ONCE":
                # For one-time reminders, there is no next occurrence
                raise InvalidConfigurationError(f"Cannot calculate next date for pattern: {pattern}")
                
            # Get just the date part, with time set to midnight
            current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # For daily reminders
            if pattern == "DAILY":
                return current_date + timedelta(days=1)
                
            # For weekly reminders
            elif pattern.startswith("WEEKLY_"):
                days_of_week = {
                    "MON": 0, "TUE": 1, "WED": 2, "THU": 3, 
                    "FRI": 4, "SAT": 5, "SUN": 6
                }
                target_day = pattern.split("_")[1]
                
                if target_day not in days_of_week:
                    raise InvalidConfigurationError(f"Invalid weekly pattern: {pattern}")
                    
                days_ahead = days_of_week[target_day] - current_date.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                
                return current_date + timedelta(days=days_ahead)
                
            # For monthly reminders
            elif pattern.startswith("MONTHLY_"):
                try:
                    # Get day of month (e.g., MONTHLY_15 for 15th of each month)
                    day_of_month = int(pattern.split("_")[1])
                    
                    if day_of_month < 1 or day_of_month > 31:
                        raise InvalidConfigurationError(f"Invalid monthly pattern day: {pattern}")
                        
                    next_date = current_date.replace(day=1) + timedelta(days=32)  # Move to next month
                    next_date = next_date.replace(day=1)  # First day of next month
                    
                    # Try to set the specific day
                    try:
                        next_date = next_date.replace(day=day_of_month)
                    except ValueError:
                        # Handle months with fewer days
                        if day_of_month > 28:
                            # Set to last day of month
                            next_month = next_date.replace(day=1, month=next_date.month+1 if next_date.month < 12 else 1, 
                                                        year=next_date.year if next_date.month < 12 else next_date.year+1)
                            next_date = next_month - timedelta(days=1)
                    
                    # If the calculated date is in the current month and has already passed
                    if next_date.month == current_date.month and next_date.day < current_date.day:
                        next_date = next_date.replace(month=next_date.month+1 if next_date.month < 12 else 1,
                                                    year=next_date.year if next_date.month < 12 else next_date.year+1)
                        
                        # Handle months with fewer days again
                        try:
                            next_date = next_date.replace(day=day_of_month)
                        except ValueError:
                            # Set to last day of month
                            next_month = next_date.replace(day=1, month=next_date.month+1 if next_date.month < 12 else 1, 
                                                        year=next_date.year if next_date.month < 12 else next_date.year+1)
                            next_date = next_month - timedelta(days=1)
                    
                    return next_date
                    
                except (ValueError, IndexError):
                    raise InvalidConfigurationError(f"Invalid monthly pattern format: {pattern}")
                    
            # For yearly reminders
            elif pattern.startswith("YEARLY_"):
                try:
                    # Format is YEARLY_MM_DD (e.g., YEARLY_12_25 for December 25)
                    parts = pattern.split("_")
                    if len(parts) != 3:
                        raise InvalidConfigurationError(f"Invalid yearly pattern format: {pattern}")
                        
                    month = int(parts[1])
                    day = int(parts[2])
                    
                    if month < 1 or month > 12 or day < 1 or day > 31:
                        raise InvalidConfigurationError(f"Invalid month/day in yearly pattern: {pattern}")
                    
                    # Try for this year first
                    try:
                        next_date = current_date.replace(month=month, day=day)
                    except ValueError:
                        # Handle invalid dates like February 30
                        raise InvalidConfigurationError(f"Invalid date in yearly pattern: {pattern}")
                    
                    # If the date has already passed this year, move to next year
                    if next_date < current_date:
                        next_date = next_date.replace(year=current_date.year + 1)
                    
                    return next_date
                    
                except (ValueError, IndexError):
                    raise InvalidConfigurationError(f"Invalid yearly pattern format: {pattern}")
            
            # Unsupported pattern
            raise InvalidConfigurationError(f"Unsupported reminder pattern: {pattern}")
            
        except InvalidConfigurationError as ice:
            # Re-raise application exceptions
            raise
        except Exception as e:
            # Log detailed error for debugging
            logger.error(f"Error calculating next reminder date: {str(e)}", exc_info=True)
            raise InvalidConfigurationError(f"Failed to calculate next date for pattern: {pattern}")
        
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