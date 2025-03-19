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
        business,  # Add business parameter
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send an SMS to a recipient using business-specific Twilio settings.
        
        Args:
            business: Business object with Twilio settings
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the SMS
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            # Check if business has Twilio configured
            if not business.twilio_account_sid or not business.twilio_auth_token or not business.twilio_phone_number:
                logger.warning(f"Business {business.id} has no Twilio settings configured, falling back to global settings")
                # Fall back to global settings if business settings not available
                account_sid = settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN
                phone_number = settings.TWILIO_PHONE_NUMBER
            else:
                # Use business-specific settings
                account_sid = business.twilio_account_sid
                auth_token = business.twilio_auth_token
                phone_number = business.twilio_phone_number
            
            # Check if Twilio credentials are configured
            if not account_sid or not auth_token or not phone_number:
                logger.error("Twilio credentials not configured")
                return False
            
            # Ensure recipient phone is in E.164 format
            if not recipient_phone.startswith('+'):
                recipient_phone = f"+{recipient_phone}"
            
            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            
            # Send the message
            message = client.messages.create(
                to=recipient_phone,
                from_=phone_number,
                body=message
            )
            
            logger.info(f"SMS sent to {recipient_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient_phone}: {str(e)}")
            return False
    
    @staticmethod
    def send_reminder_sms(
        business,  # Add business parameter
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
    ) -> bool:
        """
        Send a reminder SMS.
        
        Args:
            business: Business object with Twilio settings
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        # Create message content
        message = f"Reminder: {reminder_title} from {business.name}"
        
        # Add description if provided (keep SMS short)
        if reminder_description:
            description_preview = reminder_description[:100]
            if len(reminder_description) > 100:
                description_preview += "..."
            message += f"\n\n{description_preview}"
        
        return SMSService.send_sms(
            business=business,
            recipient_phone=recipient_phone,
            message=message,
        )