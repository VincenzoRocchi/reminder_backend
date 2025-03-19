import logging
from twilio.rest import Client
from typing import Optional

from app.core.settings import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service for sending SMS notifications using Twilio
    """
    
    @staticmethod
    def send_sms(
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send an SMS to a recipient.
        
        Args:
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the SMS
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            # Check if Twilio credentials are configured
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.error("Twilio credentials not configured")
                return False
            
            # Ensure recipient phone is in E.164 format
            if not recipient_phone.startswith('+'):
                recipient_phone = f"+{recipient_phone}"
            
            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Send the message
            message = client.messages.create(
                to=recipient_phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                body=message
            )
            
            logger.info(f"SMS sent to {recipient_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient_phone}: {str(e)}")
            return False
    
    @staticmethod
    def send_reminder_sms(
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
        business_name: str,
    ) -> bool:
        """
        Send a reminder SMS.
        
        Args:
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            business_name: Name of the business sending the reminder
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        # Create message content
        message = f"Reminder: {reminder_title} from {business_name}"
        
        # Add description if provided (keep SMS short)
        if reminder_description:
            description_preview = reminder_description[:100]
            if len(reminder_description) > 100:
                description_preview += "..."
            message += f"\n\n{description_preview}"
        
        return SMSService.send_sms(
            recipient_phone=recipient_phone,
            message=message,
        )