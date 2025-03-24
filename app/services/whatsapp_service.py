import logging
import httpx
from typing import Optional

from app.core.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Service for sending WhatsApp notifications
    """
    
    @staticmethod
    async def send_whatsapp(
        service_account,
        user,  # Add user parameter
        recipient_phone: str,
        message: str,
    ) -> bool:
        """
        Send a WhatsApp message to a recipient using service account WhatsApp API settings.
        
        Args:
            service_account: ServiceAccount object with WhatsApp API settings
            user: User who owns the service account
            recipient_phone: Phone number of the recipient (E.164 format)
            message: Content of the WhatsApp message
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Check if service account has WhatsApp API configured
            if not service_account.whatsapp_api_key or not service_account.whatsapp_api_url:
                logger.warning(f"Service account {service_account.id} has no WhatsApp API settings configured, falling back to global settings")
                # Fall back to global settings if service account settings not available
                api_key = settings.WHATSAPP_API_KEY
                api_url = settings.WHATSAPP_API_URL
            else:
                # Use service account specific settings
                api_key = service_account.whatsapp_api_key
                api_url = service_account.whatsapp_api_url
            
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
        service_account,
        user,  # Add user parameter
        recipient_phone: str,
        reminder_title: str,
        reminder_description: Optional[str],
    ) -> bool:
        """
        Send a reminder via WhatsApp.
        
        Args:
            service_account: ServiceAccount object with WhatsApp API settings
            user: User who owns the service account
            recipient_phone: Phone number of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        # Use business name if available, otherwise use username
        sender_name = user.business_name or user.username
        
        # Create message content
        message = f"*Reminder: {reminder_title}*\nFrom: {sender_name}"
        
        # Add description if provided
        if reminder_description:
            message += f"\n\n{reminder_description}"
        
        return await WhatsAppService.send_whatsapp(
            service_account=service_account,
            user=user,
            recipient_phone=recipient_phone,
            message=message,
        )