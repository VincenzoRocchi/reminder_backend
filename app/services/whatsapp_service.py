import logging
import httpx
from typing import Optional

from app.core.settings import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Service for sending WhatsApp notifications
    
    Note: This is a placeholder implementation. You'll need to replace this
    with your actual WhatsApp Business API provider (like Twilio, MessageBird, etc.)
    """
    
    @staticmethod
    async def send_whatsapp(
        business,  # Add business parameter
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send a WhatsApp message to a recipient using business-specific WhatsApp API settings.
        
        Args:
            business: Business object with WhatsApp API settings
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the WhatsApp message
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Check if business has WhatsApp API configured
            if not business.whatsapp_api_key or not business.whatsapp_api_url:
                logger.warning(f"Business {business.id} has no WhatsApp API settings configured, falling back to global settings")
                # Fall back to global settings if business settings not available
                api_key = settings.WHATSAPP_API_KEY
                api_url = settings.WHATSAPP_API_URL
            else:
                # Use business-specific settings
                api_key = business.whatsapp_api_key
                api_url = business.whatsapp_api_url
            
            # Check if WhatsApp API credentials are configured
            if not api_key or not api_url:
                logger.error("WhatsApp API credentials not configured")
                return False
            
            # Ensure recipient phone is in E.164 format
            if not recipient_phone.startswith('+'):
                recipient_phone = f"+{recipient_phone}"
            
            # Prepare the request payload
            # Note: This is a placeholder. Adjust according to your WhatsApp API provider
            payload = {
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            # Send the request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp message sent to {recipient_phone}")
                    return True
                else:
                    logger.error(f"Failed to send WhatsApp message: {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {recipient_phone}: {str(e)}")
            return False
    
    @staticmethod
    async def send_reminder_whatsapp(
        business,  # Add business parameter
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
    ) -> bool:
        """
        Send a reminder via WhatsApp.
        
        Args:
            business: Business object with WhatsApp API settings
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        # Create message content
        message = f"*Reminder: {reminder_title}*\nFrom: {business.name}"
        
        # Add description if provided
        if reminder_description:
            message += f"\n\n{reminder_description}"
        
        return await WhatsAppService.send_whatsapp(
            business=business,
            recipient_phone=recipient_phone,
            message=message,
        )