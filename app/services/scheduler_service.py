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

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for scheduling and processing reminders
    """
    
    def __init__(self):
        """Initialize the scheduler"""
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """Start the scheduler"""
        logger.info("Starting reminder scheduler service")
        
        # Add job to process reminders every minute
        self.scheduler.add_job(
            self.process_reminders,
            IntervalTrigger(minutes=1),
            id="process_reminders",
            replace_existing=True,
        )
        
        # Start the scheduler
        self.scheduler.start()
    
    async def process_reminders(self):
        """
        Process reminders that are due to be sent
        """
        logger.info("Processing due reminders")
        
        # Create a new DB session
        db = SessionLocal()
        try:
            # Get current time
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
                # Get business info
                business = db.query(Business).filter(Business.id == reminder.business_id).first()
                if not business or not business.is_active:
                    continue
                
                # Get pending notifications for this reminder
                pending_notifications = (
                    db.query(Notification)
                    .filter(
                        Notification.reminder_id == reminder.id,
                        Notification.status == ReminderStatus.PENDING
                    )
                    .all()
                )
                
                # Process each pending notification
                for notification in pending_notifications:
                    # Get recipient info
                    recipient = db.query(User).filter(User.id == notification.recipient_id).first()
                    if not recipient or not recipient.is_active:
                        continue
                    
                    # Send notification based on type
                    success = await self.send_notification(
                        notification_type=notification.notification_type,
                        recipient=recipient,
                        reminder=reminder,
                        business=business  # Pass the business object
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
                        # If can't calculate next date, deactivate the reminder
                        reminder.is_active = False
                else:
                    # Non-recurring reminder should be deactivated after sending
                    reminder.is_active = False
                
                db.add(reminder)
            
            # Commit all changes
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing reminders: {str(e)}")
        finally:
            db.close()
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: User,
        reminder: Reminder,
        business: Business  # Pass the business object
    ) -> bool:
        """
        Send a notification based on its type
        
        Args:
            notification_type: Type of notification to send
            recipient: User to receive the notification
            reminder: Reminder details
            business: Business sending the reminder
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            if notification_type == NotificationType.EMAIL:
                if not recipient.email:
                    return False
                
                return await EmailService.send_reminder_email(
                    business=business,  # Pass business
                    recipient_email=recipient.email,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description or "",
                )
                
            elif notification_type == NotificationType.SMS:
                if not recipient.phone_number:
                    return False
                
                return SMSService.send_reminder_sms(
                    business=business,  # Pass business
                    recipient_phone=recipient.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
                
            elif notification_type == NotificationType.WHATSAPP:
                if not recipient.phone_number:
                    return False
                
                return await WhatsAppService.send_reminder_whatsapp(
                    business=business,  # Pass business
                    recipient_phone=recipient.phone_number,
                    reminder_title=reminder.title,
                    reminder_description=reminder.description,
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def calculate_next_reminder_date(self, current_date: datetime, pattern: str) -> datetime:
        """
        Calculate the next reminder date based on the recurrence pattern
        
        Args:
            current_date: Current reminder date
            pattern: Recurrence pattern (e.g., 'daily', 'weekly', 'monthly')
            
        Returns:
            Next reminder date or None if pattern is invalid
        """
        try:
            pattern = pattern.lower()
            
            if pattern == 'daily':
                return current_date + timedelta(days=1)
            
            elif pattern == 'weekly':
                return current_date + timedelta(weeks=1)
            
            elif pattern == 'monthly':
                # Simple implementation - may need improvement for edge cases
                new_month = current_date.month + 1
                new_year = current_date.year
                
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                
                day = min(current_date.day, 28)  # Simple handling for month length differences
                
                return current_date.replace(year=new_year, month=new_month, day=day)
            
            elif pattern == 'yearly':
                return current_date.replace(year=current_date.year + 1)
            
            elif pattern.startswith('every '):
                # Pattern like "every 3 days" or "every 2 weeks"
                parts = pattern.split()
                if len(parts) >= 3:
                    try:
                        number = int(parts[1])
                        unit = parts[2].lower()
                        
                        if unit in ('day', 'days'):
                            return current_date + timedelta(days=number)
                        elif unit in ('week', 'weeks'):
                            return current_date + timedelta(weeks=number)
                        elif unit in ('month', 'months'):
                            # Simple implementation
                            new_month = current_date.month + number
                            new_year = current_date.year
                            
                            while new_month > 12:
                                new_month -= 12
                                new_year += 1
                            
                            day = min(current_date.day, 28)
                            
                            return current_date.replace(year=new_year, month=new_month, day=day)
                    except ValueError:
                        pass
            
            # If pattern is not recognized
            logger.warning(f"Unrecognized recurrence pattern: {pattern}")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating next reminder date: {str(e)}")
            return None
        
        # Add to the existing SchedulerService class
    def __str__(self):
        status = "running" if hasattr(self, 'scheduler') and getattr(self.scheduler, 'running', False) else "stopped"
        job_count = len(self.scheduler.get_jobs()) if hasattr(self, 'scheduler') else 0
        return f"Reminder Scheduler Service ({status}, {job_count} jobs)"

    def __repr__(self):
        if hasattr(self, 'scheduler'):
            status = 'running' if getattr(self.scheduler, 'running', False) else 'stopped'
            job_count = len(self.scheduler.get_jobs())
        else:
            status = 'uninitialized'
            job_count = 0
        return f"<SchedulerService status={status} jobs={job_count}>"


# Create a singleton instance
scheduler_service = SchedulerService()