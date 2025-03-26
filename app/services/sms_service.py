# app/services/sms_service.py
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
        service_account,
        user,  # Add user parameter
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send an SMS to a recipient using service account Twilio settings.
        
        Args:
            service_account: ServiceAccount object with Twilio settings
            user: User who owns the service account
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the SMS
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            # Import secrets manager here to avoid circular imports
            from app.core.secrets_manager import secrets_manager
            
            # Check if service account has Twilio configured
            if not service_account.twilio_account_sid or not service_account.twilio_auth_token:
                logger.warning(f"Service account {service_account.id} has incomplete Twilio settings, checking secrets")
                
                # Try to get secrets first
                try:
                    sms_secrets = secrets_manager.get_category("sms")
                    account_sid = service_account.twilio_account_sid or sms_secrets.get("twilio_account_sid") or settings.TWILIO_ACCOUNT_SID
                    auth_token = service_account.twilio_auth_token or sms_secrets.get("twilio_auth_token") or settings.TWILIO_AUTH_TOKEN
                    phone_number = service_account.twilio_phone_number or sms_secrets.get("twilio_phone_number") or settings.TWILIO_PHONE_NUMBER
                except Exception as e:
                    # Fall back to settings if secrets fail
                    logger.warning(f"Error accessing SMS secrets: {str(e)}")
                    account_sid = service_account.twilio_account_sid or settings.TWILIO_ACCOUNT_SID
                    auth_token = service_account.twilio_auth_token or settings.TWILIO_AUTH_TOKEN
                    phone_number = service_account.twilio_phone_number or settings.TWILIO_PHONE_NUMBER
            else:
                # Use service account specific settings
                account_sid = service_account.twilio_account_sid
                auth_token = service_account.twilio_auth_token
                phone_number = service_account.twilio_phone_number
            
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
        service_account,
        user,  # Add user parameter
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
    ) -> bool:
        """
        Send a reminder SMS.
        
        Args:
            service_account: ServiceAccount object with Twilio settings
            user: User who owns the service account
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        # Use business name if available, otherwise use username
        sender_name = user.business_name or user.username
        
        # Create message content
        message = f"Reminder: {reminder_title} from {sender_name}"
        
        # Add description if provided (keep SMS short)
        if reminder_description:
            description_preview = reminder_description[:100]
            if len(reminder_description) > 100:
                description_preview += "..."
            message += f"\n\n{description_preview}"
        
        return SMSService.send_sms(
            service_account=service_account,
            user=user,
            recipient_phone=recipient_phone,
            message=message,
        )