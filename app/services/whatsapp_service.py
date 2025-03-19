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
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send a WhatsApp message to a recipient.
        
        Args:
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the WhatsApp message
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Check if WhatsApp API credentials are configured
            if not settings.WHATSAPP_API_KEY or not settings.WHATSAPP_API_URL:
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
                    settings.WHATSAPP_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
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
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
        business_name: str,
    ) -> bool:
        """
        Send a reminder via WhatsApp.
        
        Args:
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            business_name: Name of the business sending the reminder
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        # Create message content
        message = f"*Reminder: {reminder_title}*\nFrom: {business_name}"
        
        # Add description if provided
        if reminder_description:
            message += f"\n\n{reminder_description}"
        
        return await WhatsAppService.send_whatsapp(
            recipient_phone=recipient_phone,
            message=message,
        )