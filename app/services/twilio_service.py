# app/services/twilio_service.py
import logging
from twilio.rest import Client
from typing import Optional, Literal, Tuple

from app.core.settings import settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class TwilioService:
    """
    Unified service for sending SMS and WhatsApp notifications using Twilio.
    
    This service consolidates both SMS and WhatsApp functionality since
    both can be handled through Twilio's API with similar parameters.
    """
    
    @staticmethod
    def get_twilio_credentials() -> Tuple[str, str]:
        """
        Get Twilio credentials from settings.
        
        Returns:
            Tuple containing (account_sid, auth_token)
            
        Raises:
            ServiceError: If credentials are not configured
        """
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            
            if not account_sid or not auth_token:
                logger.warning("Twilio credentials not configured in environment variables")
                raise ServiceError("twilio", "Twilio credentials not configured in environment variables")
                
            return account_sid, auth_token
            
        except Exception as e:
            logger.error(f"Error getting Twilio credentials: {str(e)}")
            raise ServiceError("twilio", "Failed to get Twilio credentials", str(e))
    
    @staticmethod
    def send_message(
        user,
        recipient_phone: str,
        message: str,
        from_phone_number: str,
        channel: Literal["sms", "whatsapp"] = "sms",
        track_usage: bool = True,
    ) -> bool:
        """
        Send a message via SMS or WhatsApp using Twilio.
        
        Args:
            user: User who is sending the message (for tracking)
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the message
            from_phone_number: Phone number to send from (client's Twilio number)
            channel: Channel to use ("sms" or "whatsapp")
            track_usage: Whether to track usage for billing
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Get Twilio credentials
            account_sid, auth_token = TwilioService.get_twilio_credentials()
            
            # Check if Twilio credentials are configured
            if not account_sid or not auth_token:
                logger.error("Twilio credentials not configured")
                return False
                
            # Check if from phone number is provided
            if not from_phone_number:
                logger.error("From phone number is required")
                return False
            
            # Ensure phone numbers are in E.164 format
            if not recipient_phone.startswith('+'):
                recipient_phone = f"+{recipient_phone}"
                
            if not from_phone_number.startswith('+'):
                from_phone_number = f"+{from_phone_number}"
            
            # Prepare the from number based on channel
            if channel == "whatsapp":
                from_number = f"whatsapp:{from_phone_number}"
                to_number = f"whatsapp:{recipient_phone}"
            else:  # SMS
                from_number = from_phone_number
                to_number = recipient_phone
            
            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            
            # Send the message
            message_result = client.messages.create(
                to=to_number,
                from_=from_number,
                body=message
            )
            
            logger.info(f"{channel.upper()} sent to {recipient_phone} from {from_phone_number}, SID: {message_result.sid}")
            
            # Track usage for billing if requested
            if track_usage and user:
                # In production, use a non-blocking approach like a background task
                # or message queue to avoid slowing down the request
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    # Update the appropriate counter based on channel
                    if channel == "whatsapp":
                        user.whatsapp_count = user.whatsapp_count + 1 if hasattr(user, 'whatsapp_count') else 1
                    else:  # SMS
                        user.sms_count = user.sms_count + 1 if hasattr(user, 'sms_count') else 1
                    
                    db.add(user)
                    db.commit()
                    logger.info(f"{channel.upper()} usage tracked for user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to track {channel.upper()} usage: {str(e)}")
                    db.rollback()
                finally:
                    db.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send {channel.upper()} to {recipient_phone}: {str(e)}")
            raise ServiceError(channel, f"Failed to send {channel}", str(e))
    
    @staticmethod
    def send_sms(
        user,
        recipient_phone: str,
        message: str,
        from_phone_number: str,
        track_usage: bool = True,
    ) -> bool:
        """
        Send an SMS via Twilio (convenience method).
        
        Args:
            user: User who is sending the message (for tracking)
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the SMS
            from_phone_number: Phone number to send from (client's Twilio number)
            track_usage: Whether to track usage for billing
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        return TwilioService.send_message(
            user=user,
            recipient_phone=recipient_phone,
            message=message,
            from_phone_number=from_phone_number,
            channel="sms",
            track_usage=track_usage
        )
    
    @staticmethod
    def send_whatsapp(
        user, 
        recipient_phone: str,
        message: str,
        from_phone_number: str,
        track_usage: bool = True,
    ) -> bool:
        """
        Send a WhatsApp message via Twilio (convenience method).
        
        Args:
            user: User who is sending the message (for tracking)
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the WhatsApp message
            from_phone_number: Phone number to send from (client's Twilio number)
            track_usage: Whether to track usage for billing
            
        Returns:
            True if WhatsApp message was sent successfully, False otherwise
        """
        return TwilioService.send_message(
            user=user,
            recipient_phone=recipient_phone,
            message=message,
            from_phone_number=from_phone_number,
            channel="whatsapp",
            track_usage=track_usage
        )
    
    @staticmethod
    def send_reminder_message(
        user,
        recipient_phone: str,
        reminder_title: str,
        from_phone_number: str,
        reminder_description: Optional[str] = None,
        sender_identity = None,
        channel: Literal["sms", "whatsapp"] = "sms",
    ) -> bool:
        """
        Send a reminder message via SMS or WhatsApp.
        
        Args:
            user: User sending the reminder
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            from_phone_number: Phone number to send from (client's Twilio number)
            reminder_description: Description of the reminder
            sender_identity: Optional SenderIdentity object for customizing from name
            channel: Channel to use ("sms" or "whatsapp")
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        # Use display name from sender identity if available
        sender_name = (sender_identity.display_name 
                      if sender_identity 
                      else (user.business_name or user.username))
        
        # Create message content (slightly different formatting based on channel)
        if channel == "whatsapp":
            # WhatsApp supports basic markdown
            message = f"*Reminder: {reminder_title}*\nFrom: {sender_name}"
            
            # Add description if provided (WhatsApp can handle longer messages)
            if reminder_description:
                message += f"\n\n{reminder_description}"
        else:
            # Plain SMS (keep it shorter)
            message = f"Reminder: {reminder_title} from {sender_name}"
            
            # Add description if provided (limit length for SMS)
            if reminder_description:
                description_preview = reminder_description[:100]
                if len(reminder_description) > 100:
                    description_preview += "..."
                message += f"\n\n{description_preview}"
        
        return TwilioService.send_message(
            user=user,
            recipient_phone=recipient_phone,
            message=message,
            from_phone_number=from_phone_number,
            channel=channel
        ) 