import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.email_service import EmailService
from app.core.exceptions import ServiceError


@pytest.mark.asyncio
async def test_send_email_success():
    """Test sending an email successfully"""
    # Create mock email configuration
    email_config = MagicMock()
    email_config.smtp_host = "smtp.example.com"
    email_config.smtp_port = 587
    email_config.smtp_user = "user@example.com"
    email_config.smtp_password = "password"
    email_config.email_from = "sender@example.com"
    
    # Mock aiosmtplib.send
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        # Send email
        result = await EmailService.send_email(
            email_configuration=email_config,
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            cc=["cc@example.com"],
            html_content="<p>Test HTML</p>"
        )
        
        # Check result
        assert result is True
        
        # Check that send was called with correct arguments
        mock_send.assert_called_once()
        
        # Check the message contents from the call
        call_args = mock_send.call_args[1]
        assert call_args["hostname"] == "smtp.example.com"
        assert call_args["port"] == 587
        assert call_args["username"] == "user@example.com"
        assert call_args["password"] == "password"
        assert call_args["use_tls"] is True
        
        # Check the message object
        message = mock_send.call_args[0][0]
        assert message["From"] == "sender@example.com"
        assert message["To"] == "recipient@example.com"
        assert message["Subject"] == "Test Subject"
        assert message["Cc"] == "cc@example.com"
        
        # The message should have both text and HTML parts
        assert message.is_multipart()
        parts = list(message.walk())
        assert len(parts) == 3  # 1 multipart container + 1 text part + 1 HTML part
        
        # Check text part
        text_part = parts[1]
        assert text_part.get_content_type() == "text/plain"
        assert text_part.get_payload() == "Test body"
        
        # Check HTML part
        html_part = parts[2]
        assert html_part.get_content_type() == "text/html"
        assert html_part.get_payload() == "<p>Test HTML</p>"


@pytest.mark.asyncio
async def test_send_email_without_html():
    """Test sending an email without HTML content"""
    # Create mock email configuration
    email_config = MagicMock()
    email_config.smtp_host = "smtp.example.com"
    email_config.smtp_port = 587
    email_config.smtp_user = "user@example.com"
    email_config.smtp_password = "password"
    email_config.email_from = "sender@example.com"
    
    # Mock aiosmtplib.send
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        # Send email
        result = await EmailService.send_email(
            email_configuration=email_config,
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        # Check result
        assert result is True
        
        # Check the message contents
        message = mock_send.call_args[0][0]
        
        # The message should have just text part
        parts = list(message.walk())
        assert len(parts) == 2  # 1 multipart container + 1 text part
        
        # Check text part
        text_part = parts[1]
        assert text_part.get_content_type() == "text/plain"
        assert text_part.get_payload() == "Test body"


@pytest.mark.asyncio
async def test_send_email_without_cc():
    """Test sending an email without CC recipients"""
    # Create mock email configuration
    email_config = MagicMock()
    email_config.smtp_host = "smtp.example.com"
    email_config.smtp_port = 587
    email_config.smtp_user = "user@example.com"
    email_config.smtp_password = "password"
    email_config.email_from = "sender@example.com"
    
    # Mock aiosmtplib.send
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        # Send email
        result = await EmailService.send_email(
            email_configuration=email_config,
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            html_content="<p>Test HTML</p>"
        )
        
        # Check result
        assert result is True
        
        # Check the message contents
        message = mock_send.call_args[0][0]
        
        # The CC header should not be present
        assert "Cc" not in message


@pytest.mark.asyncio
async def test_send_email_incomplete_config():
    """Test sending an email with incomplete configuration"""
    # Create mock email configuration with missing settings
    email_config = MagicMock()
    email_config.smtp_host = None  # Missing host
    email_config.smtp_port = 587
    email_config.smtp_user = "user@example.com"
    email_config.smtp_password = "password"
    email_config.email_from = "sender@example.com"
    
    # Should log error and return False
    with patch('app.services.email_service.logger') as mock_logger:
        result = await EmailService.send_email(
            email_configuration=email_config,
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        # Check result
        assert result is False
        
        # Check that error was logged
        mock_logger.error.assert_called_once()
        assert "incomplete" in mock_logger.error.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_send_email_exception():
    """Test handling exceptions when sending an email"""
    # Create mock email configuration
    email_config = MagicMock()
    email_config.smtp_host = "smtp.example.com"
    email_config.smtp_port = 587
    email_config.smtp_user = "user@example.com"
    email_config.smtp_password = "password"
    email_config.email_from = "sender@example.com"
    
    # Mock aiosmtplib.send to raise an exception
    error_msg = "Connection refused"
    with patch('app.services.email_service.aiosmtplib.send', 
              new_callable=AsyncMock, 
              side_effect=Exception(error_msg)) as mock_send:
        # Mock logger
        with patch('app.services.email_service.logger') as mock_logger:
            # Should raise ServiceError
            with pytest.raises(ServiceError) as excinfo:
                await EmailService.send_email(
                    email_configuration=email_config,
                    recipient_email="recipient@example.com",
                    subject="Test Subject",
                    body="Test body"
                )
            
            # Check exception message
            assert "failed to send email" in str(excinfo.value).lower()
            assert error_msg in str(excinfo.value)
            
            # Check that error was logged
            mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_send_reminder_email():
    """Test sending a reminder email"""
    # Create mock objects
    email_config = MagicMock()
    user = MagicMock()
    user.id = 123
    sender_identity = MagicMock()
    sender_identity.display_name = "Test Sender"
    
    # Mock send_email
    with patch.object(EmailService, 'send_email', new_callable=AsyncMock, return_value=True) as mock_send:
        # Send reminder email
        result = await EmailService.send_reminder_email(
            email_configuration=email_config,
            user=user,
            recipient_email="recipient@example.com",
            reminder_title="Reminder Title",
            reminder_description="Reminder description",
            sender_identity=sender_identity
        )
        
        # Check result
        assert result is True
        
        # Check send_email call
        mock_send.assert_called_once()
        
        # Check call arguments
        call_args = mock_send.call_args[1]
        assert call_args["email_configuration"] == email_config
        assert call_args["recipient_email"] == "recipient@example.com"
        assert "Reminder Title" in call_args["subject"]
        assert "Reminder Title" in call_args["body"]
        assert "Reminder description" in call_args["body"]
        assert "Test Sender" in call_args["body"]
        
        # HTML content should be provided
        assert call_args["html_content"] is not None
        assert "Reminder Title" in call_args["html_content"]
        assert "Reminder description" in call_args["html_content"]
        assert "Test Sender" in call_args["html_content"]


@pytest.mark.asyncio
async def test_send_reminder_email_without_sender_identity():
    """Test sending a reminder email without sender identity"""
    # Create mock objects
    email_config = MagicMock()
    user = MagicMock()
    user.id = 123
    
    # Mock send_email
    with patch.object(EmailService, 'send_email', new_callable=AsyncMock, return_value=True) as mock_send:
        # Send reminder email without sender identity
        result = await EmailService.send_reminder_email(
            email_configuration=email_config,
            user=user,
            recipient_email="recipient@example.com",
            reminder_title="Reminder Title",
            reminder_description="Reminder description"
        )
        
        # Check result
        assert result is True
        
        # Check send_email call
        mock_send.assert_called_once()
        
        # Check call arguments
        call_args = mock_send.call_args[1]
        # Body and HTML should not contain sender identity
        assert "from" not in call_args["body"].lower()
        assert "from" not in call_args["html_content"].lower()


@pytest.mark.asyncio
async def test_send_reminder_email_exception():
    """Test handling exceptions when sending a reminder email"""
    # Create mock objects
    email_config = MagicMock()
    user = MagicMock()
    user.id = 123
    
    # Mock send_email to raise an exception
    error_msg = "Email sending failed"
    with patch.object(EmailService, 'send_email', 
                     new_callable=AsyncMock, 
                     side_effect=Exception(error_msg)) as mock_send:
        # Mock logger
        with patch('app.services.email_service.logger') as mock_logger:
            # Send reminder email
            result = await EmailService.send_reminder_email(
                email_configuration=email_config,
                user=user,
                recipient_email="recipient@example.com",
                reminder_title="Reminder Title",
                reminder_description="Reminder description"
            )
            
            # Should return False on error
            assert result is False
            
            # Check that error was logged
            mock_logger.error.assert_called_once()
            assert error_msg in mock_logger.error.call_args[0][0] 