# app/services/email_service.py
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.core.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending email notifications
    """
    
    @staticmethod
    async def send_email(
        service_account,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        html_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email to a recipient using service account SMTP settings.
        
        Args:
            service_account: ServiceAccount object with SMTP settings
            recipient_email: Email address of the recipient
            subject: Subject of the email
            body: Text content of the email
            cc: List of email addresses to CC
            html_content: Optional HTML content of the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Import secrets manager here to avoid circular imports
            from app.core.secrets_manager import secrets_manager
            
            # Check if service account has SMTP configured
            if not service_account.smtp_host or not service_account.smtp_user or not service_account.smtp_password:
                logger.warning(f"Service account {service_account.id} has incomplete SMTP settings, checking secrets")
                
                # Try to get from secrets first
                try:
                    email_secrets = secrets_manager.get_category("email")
                    smtp_host = service_account.smtp_host or email_secrets.get("smtp_host") or settings.SMTP_HOST
                    smtp_port = service_account.smtp_port or email_secrets.get("smtp_port", 0) or settings.SMTP_PORT
                    smtp_user = service_account.smtp_user or email_secrets.get("smtp_user") or settings.SMTP_USER
                    smtp_password = service_account.smtp_password or email_secrets.get("smtp_password") or settings.SMTP_PASSWORD
                    email_from = service_account.email_from or email_secrets.get("email_from") or settings.EMAIL_FROM
                except Exception as e:
                    # Fall back to settings if secrets fail
                    logger.warning(f"Error accessing email secrets: {str(e)}")
                    smtp_host = service_account.smtp_host or settings.SMTP_HOST
                    smtp_port = service_account.smtp_port or settings.SMTP_PORT
                    smtp_user = service_account.smtp_user or settings.SMTP_USER
                    smtp_password = service_account.smtp_password or settings.SMTP_PASSWORD
                    email_from = service_account.email_from or settings.EMAIL_FROM
            else:
                # Use service account specific settings
                smtp_host = service_account.smtp_host
                smtp_port = service_account.smtp_port
                smtp_user = service_account.smtp_user
                smtp_password = service_account.smtp_password
                email_from = service_account.email_from or settings.EMAIL_FROM
            
            message = MIMEMultipart('alternative')
            message['From'] = email_from
            message['To'] = recipient_email
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            # Attach text part
            message.attach(MIMEText(body, 'plain'))
            
            # Attach HTML part if provided
            if html_content:
                message.attach(MIMEText(html_content, 'html'))
            
            # Send the email
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port or 587,
                username=smtp_user,
                password=smtp_password,
                use_tls=True,
            )
            
            logger.info(f"Email sent to {recipient_email} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_reminder_email(
        service_account,
        user,  # Add user parameter to get business name or username
        recipient_email: str,
        reminder_title: str,
        reminder_description: str,
    ) -> bool:
        """
        Send a reminder email.
        
        Args:
            service_account: ServiceAccount object with SMTP settings
            user: User who owns the service account
            recipient_email: Email address of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Use business name if available, otherwise use username
        sender_name = user.business_name or user.username
        
        subject = f"Reminder: {reminder_title} from {sender_name}"
        
        # Create text content
        text_content = f"""
        Reminder: {reminder_title}
        
        {reminder_description}
        
        This reminder was sent by {sender_name}.
        """
        
        # Create HTML content
        html_content = f"""
        <html>
            <body>
                <h2>Reminder: {reminder_title}</h2>
                <p>{reminder_description}</p>
                <br>
                <p><em>This reminder was sent by {sender_name}.</em></p>
            </body>
        </html>
        """
        
        return await EmailService.send_email(
            service_account=service_account,
            recipient_email=recipient_email,
            subject=subject,
            body=text_content,
            html_content=html_content,
        )