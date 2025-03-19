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
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        html_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email to a recipient.
        
        Args:
            recipient_email: Email address of the recipient
            subject: Subject of the email
            body: Text content of the email
            cc: List of email addresses to CC
            html_content: Optional HTML content of the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart('alternative')
            message['From'] = settings.EMAIL_FROM
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
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
            )
            
            logger.info(f"Email sent to {recipient_email} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_reminder_email(
        recipient_email: str,
        reminder_title: str,
        reminder_description: str,
        business_name: str,
    ) -> bool:
        """
        Send a reminder email.
        
        Args:
            recipient_email: Email address of the recipient
            reminder_title: Title of the reminder
            reminder_description: Description of the reminder
            business_name: Name of the business sending the reminder
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"Reminder: {reminder_title} from {business_name}"
        
        # Create text content
        text_content = f"""
        Reminder: {reminder_title}
        
        {reminder_description}
        
        This reminder was sent by {business_name}.
        """
        
        # Create HTML content
        html_content = f"""
        <html>
            <body>
                <h2>Reminder: {reminder_title}</h2>
                <p>{reminder_description}</p>
                <br>
                <p><em>This reminder was sent by {business_name}.</em></p>
            </body>
        </html>
        """
        
        return await EmailService.send_email(
            recipient_email=recipient_email,
            subject=subject,
            body=text_content,
            html_content=html_content,
        )