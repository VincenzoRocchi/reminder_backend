# app/services/email_service.py
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.core.settings import settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending email notifications
    """
    
    @staticmethod
    async def send_email(
        email_configuration,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        html_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email to a recipient using email configuration SMTP settings.
        
        Args:
            email_configuration: EmailConfiguration object with SMTP settings
            recipient_email: Email address of the recipient
            subject: Subject of the email
            body: Text content of the email
            cc: List of email addresses to CC
            html_content: Optional HTML content of the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Check if email configuration is complete
            if not email_configuration.smtp_host or not email_configuration.smtp_user or not email_configuration.smtp_password:
                logger.error(f"Email configuration {email_configuration.id} has incomplete SMTP settings")
                return False
            
            # Use email configuration settings
            smtp_host = email_configuration.smtp_host
            smtp_port = email_configuration.smtp_port
            smtp_user = email_configuration.smtp_user
            smtp_password = email_configuration.smtp_password
            email_from = email_configuration.email_from
            
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
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                use_tls=True,
            )
            
            logger.info(f"Email sent to {recipient_email} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            raise ServiceError("email", "Failed to send email", str(e))
    
    @staticmethod
    async def send_reminder_email(
        email_configuration,
        user,
        recipient_email: str,
        reminder_title: str,
        reminder_description: str,
        sender_identity=None,
    ) -> bool:
        """
        Send a reminder email.
        
        Args:
            email_configuration: EmailConfiguration object with SMTP settings
            user: User who owns the email configuration
            recipient_email: Email address of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            sender_identity: Optional SenderIdentity object for customizing from name
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Use sender identity display name if available, otherwise use business name or username
        sender_name = user.business_name or user.username
        if sender_identity and sender_identity.identity_type == "EMAIL":
            sender_name = sender_identity.display_name
        
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
            email_configuration=email_configuration,
            recipient_email=recipient_email,
            subject=subject,
            body=text_content,
            html_content=html_content,
        )