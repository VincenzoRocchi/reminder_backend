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
        business,  # Add business parameter
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        html_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email to a recipient using business-specific SMTP settings.
        
        Args:
            business: Business object with SMTP settings
            recipient_email: Email address of the recipient
            subject: Subject of the email
            body: Text content of the email
            cc: List of email addresses to CC
            html_content: Optional HTML content of the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Check if business has SMTP configured
            if not business.smtp_host or not business.smtp_user or not business.smtp_password:
                logger.warning(f"Business {business.id} has no SMTP settings configured, falling back to global settings")
                # Fall back to global settings if business settings not available
                smtp_host = settings.SMTP_HOST
                smtp_port = settings.SMTP_PORT
                smtp_user = settings.SMTP_USER
                smtp_password = settings.SMTP_PASSWORD
                email_from = settings.EMAIL_FROM
            else:
                # Use business-specific settings
                smtp_host = business.smtp_host
                smtp_port = business.smtp_port
                smtp_user = business.smtp_user
                smtp_password = business.smtp_password
                email_from = business.email_from or business.email or settings.EMAIL_FROM
            
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
        business,  # Add business parameter
        recipient_email: str,
        reminder_title: str,
        reminder_description: str,
    ) -> bool:
        """
        Send a reminder email.
        
        Args:
            business: Business object with SMTP settings
            recipient_email: Email address of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"Reminder: {reminder_title} from {business.name}"
        
        # Create text content
        text_content = f"""
        Reminder: {reminder_title}
        
        {reminder_description}
        
        This reminder was sent by {business.name}.
        """
        
        # Create HTML content
        html_content = f"""
        <html>
            <body>
                <h2>Reminder: {reminder_title}</h2>
                <p>{reminder_description}</p>
                <br>
                <p><em>This reminder was sent by {business.name}.</em></p>
            </body>
        </html>
        """
        
        return await EmailService.send_email(
            business=business,
            recipient_email=recipient_email,
            subject=subject,
            body=text_content,
            html_content=html_content,
        )