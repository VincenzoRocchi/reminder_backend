# app/services/sms_service.py
import logging
from twilio.rest import Client
from typing import Optional

from app.core.settings import settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class SMSService:
    """
    Service for sending SMS notifications using the platform's Twilio account
    """
    
    @staticmethod
    def send_sms(
        user,
        recipient_phone: str,
        message: str,
        track_usage: bool = True,
    ) -> bool:
        """
        Send an SMS to a recipient using the platform's Twilio settings.
        
        Args:
            user: User who is sending the message (for tracking)
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the SMS
            track_usage: Whether to track usage for billing
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            # Import secrets manager here to avoid circular imports
            from app.core.secrets_manager import secrets_manager
            
            # Get Twilio credentials from platform settings
            try:
                sms_secrets = secrets_manager.get_category("sms")
                account_sid = sms_secrets.get("twilio_account_sid") or settings.TWILIO_ACCOUNT_SID
                auth_token = sms_secrets.get("twilio_auth_token") or settings.TWILIO_AUTH_TOKEN
                phone_number = sms_secrets.get("twilio_phone_number") or settings.TWILIO_PHONE_NUMBER
            except Exception as e:
                # Fall back to settings if secrets fail
                logger.warning(f"Error accessing SMS secrets: {str(e)}")
                account_sid = settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN
                phone_number = settings.TWILIO_PHONE_NUMBER
            
            # Check if Twilio credentials are configured
            if not account_sid or not auth_token or not phone_number:
                logger.error("Platform Twilio credentials not configured")
                return False
            
            # Ensure recipient phone is in E.164 format
            if not recipient_phone.startswith('+'):
                recipient_phone = f"+{recipient_phone}"
            
            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            
            # Send the message
            message_result = client.messages.create(
                to=recipient_phone,
                from_=phone_number,
                body=message
            )
            
            logger.info(f"SMS sent to {recipient_phone}, SID: {message_result.sid}")
            
            # Track usage for billing if requested
            if track_usage and user:
                # In production, use a non-blocking approach like a background task
                # or message queue to avoid slowing down the request
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    user.sms_count += 1
                    db.add(user)
                    db.commit()
                    logger.info(f"SMS usage tracked for user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to track SMS usage: {str(e)}")
                    db.rollback()
                finally:
                    db.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient_phone}: {str(e)}")
            raise ServiceError("sms", "Failed to send SMS", str(e))
    
    @staticmethod
    def send_reminder_sms(
        user,
        sender_identity,
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
    ) -> bool:
        """
        Send a reminder SMS.
        
        Args:
            user: User sending the reminder
            sender_identity: Sender identity to use (for display name)
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        # Use display name from sender identity if available
        sender_name = sender_identity.display_name if sender_identity else (user.business_name or user.username)
        
        # Create message content
        message = f"Reminder: {reminder_title} from {sender_name}"
        
        # Add description if provided (keep SMS short)
        if reminder_description:
            description_preview = reminder_description[:100]
            if len(reminder_description) > 100:
                description_preview += "..."
            message += f"\n\n{description_preview}"
        
        return SMSService.send_sms(
            user=user,
            recipient_phone=recipient_phone,
            message=message,
        )