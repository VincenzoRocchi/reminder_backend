import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import SessionLocal
from app.models.reminder import Reminder, NotificationType
from app.models.notification import Notification, ReminderStatus
from app.models.user import User
from app.models.business import Business
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.whatsapp_service import WhatsAppService

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
        
        This method is the core business logic for reminder processing:
        1. Retrieves active reminders that have reached their scheduled time
        2. For each reminder, processes all pending notifications
        3. Handles recurring reminders by calculating the next occurrence
        4. Updates reminder and notification statuses
        
        Database transactions ensure data consistency even if errors occur.
        """
        logger.info("Processing due reminders")
        
        # Create a new DB session for this processing cycle
        # This ensures DB connection isolation and proper resource cleanup
        db = SessionLocal()
        try:
            # Get current time for comparison with reminder scheduled times
            now = datetime.now()
            
            # Find reminders that are due and active
            # The dual filter ensures we only process relevant reminders
            due_reminders = (
                db.query(Reminder)
                .filter(
                    Reminder.reminder_date <= now,  # Due or overdue reminders
                    Reminder.is_active == True      # Only process active reminders
                )
                .all()
            )
            
            # Process each due reminder individually
            for reminder in due_reminders:
                # Get business info - we need to verify business is active
                # This prevents sending reminders for deactivated businesses
                business = db.query(Business).filter(Business.id == reminder.business_id).first()
                if not business or not business.is_active:
                    # Skip reminders for inactive businesses
                    # This is a safeguard against notifications for decommissioned accounts
                    continue
                
                # Get pending notifications for this reminder
                # We only process notifications that haven't been sent yet
                pending_notifications = (
                    db.query(Notification)
                    .filter(
                        Notification.reminder_id == reminder.id,
                        Notification.status == ReminderStatus.PENDING
                    )
                    .all()
                )
                
                # Process each pending notification for this reminder
                for notification in pending_notifications:
                    # Get recipient info - we need to verify recipient is active
                    # This prevents sending to deactivated or removed users
                    recipient = db.query(User).filter(User.id == notification.recipient_id).first()
                    if not recipient or not recipient.is_active:
                        # Skip notifications for inactive recipients
                        continue
                    
                    # Send notification based on the configured channel type
                    # This polymorphic approach allows flexible notification channels
                    success = await self.send_notification(
                        notification_type=notification.notification_type,
                        recipient=recipient,
                        reminder=reminder,
                        business=business  # Pass business for branding/sender information
                    )
                    
                    # Update notification status based on send result
                    # This provides an audit trail of notification attempts
                    notification.sent_at = datetime.now()
                    if success:
                        notification.status = ReminderStatus.SENT
                    else:
                        notification.status = ReminderStatus.FAILED
                        notification.error_message = "Failed to send notification"
                    
                    # Mark notification for update in database
                    db.add(notification)
                
                # Handle recurring reminders
                # If the reminder is configured to repeat, calculate the next occurrence
                if reminder.is_recurring and reminder.recurrence_pattern:
                    # Calculate the next reminder date based on pattern
                    next_date = self.calculate_next_reminder_date(
                        reminder.reminder_date, reminder.recurrence_pattern
                    )
                    if next_date:
                        # Update reminder with new future date
                        reminder.reminder_date = next_date
                    else:
                        # If pattern is invalid, deactivate to prevent endless retries
                        reminder.is_active = False
                        logger.warning(
                            f"Deactivating reminder {reminder.id} due to invalid recurrence pattern: "
                            f"'{reminder.recurrence_pattern}'"
                        )
                else:
                    # Non-recurring reminders are one-time only
                    # Deactivate after processing to prevent duplicate sending
                    reminder.is_active = False
                
                # Mark reminder for update in database
                db.add(reminder)
            
            # Commit all changes in a single transaction
            # This ensures atomic updates and prevents partial state changes
            db.commit()
            
        except Exception as e:
            # Log detailed error information for troubleshooting
            # This provides operational visibility for production monitoring
            logger.error(f"Error processing reminders: {str(e)}", exc_info=True)
            
            # No explicit rollback needed as it will happen in the finally block
            # when the session is closed without a prior commit
        finally:
            # Always close the DB session to prevent connection leaks
            # This is crucial for long-running services to maintain DB health
            db.close()
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: User,
        reminder: Reminder,
        business: Business  # Business context for the notification
    ) -> bool:
        """
        Send a notification based on its configured channel type.
        
        This method routes the notification to the appropriate service
        based on the notification type, ensuring proper formatting and
        delivery for each channel.
        
        Args:
            notification_type: Channel to use (EMAIL, SMS, WHATSAPP)
            recipient: User object containing contact information
            reminder: Reminder details including title and description
            business: Business object for sender information and branding
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Route to appropriate notification service based on type
            # Each channel has specific requirements and formatting
            
            if notification_type == NotificationType.EMAIL:
                # Email notifications require a valid email address
                if not recipient.email:
                    logger.warning(
                        f"Cannot send email notification: Missing email for user {recipient.id}"
                    )
                    return False
                
                # Use email service to format and send the message
                # Await ensures we get the actual result before proceeding
                return await EmailService.send_reminder_email(
                    business=business,  # For email branding and sender info
                    recipient_email=recipient.email,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description or "",  # Handle null description
                )
                
            elif notification_type == NotificationType.SMS:
                # SMS notifications require a valid phone number
                if not recipient.phone_number:
                    logger.warning(
                        f"Cannot send SMS notification: Missing phone number for user {recipient.id}"
                    )
                    return False
                
                # Use SMS service to format and send the text message
                # Note: Not async - assumed to be a synchronous operation
                return SMSService.send_reminder_sms(
                    business=business,  # For sender identification
                    recipient_phone=recipient.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
                
            elif notification_type == NotificationType.WHATSAPP:
                # WhatsApp notifications require a valid phone number
                if not recipient.phone_number:
                    logger.warning(
                        f"Cannot send WhatsApp notification: Missing phone number for user {recipient.id}"
                    )
                    return False
                
                # Use WhatsApp service to format and send the message
                # Await ensures we get the actual result before proceeding
                return await WhatsAppService.send_reminder_whatsapp(
                    business=business,  # For sender identification
                    recipient_phone=recipient.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
            
            # Handle unsupported notification types
            logger.error(f"Unsupported notification type: {notification_type}")
            return False
            
        except Exception as e:
            # Log detailed error for operational monitoring
            # Capture service-specific failures for troubleshooting
            logger.error(
                f"Error sending {notification_type} notification: {str(e)}", 
                exc_info=True
            )
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