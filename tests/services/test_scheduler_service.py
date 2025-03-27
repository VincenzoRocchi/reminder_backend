import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.scheduler_service import SchedulerService
from app.models.reminders import Reminder, NotificationTypeEnum
from app.models.users import User
from app.models.clients import Client
from app.models.notifications import Notification, NotificationStatusEnum


@pytest.fixture
def scheduler_service():
    """Create a scheduler service instance without starting it"""
    service = SchedulerService()
    return service


def test_scheduler_service_initialization():
    """Test that the scheduler service initializes correctly"""
    scheduler = SchedulerService()
    
    # Check that the scheduler is initialized but not started
    assert hasattr(scheduler, "scheduler")
    assert not getattr(scheduler.scheduler, "running", False)


@patch('app.services.scheduler_service.settings')
def test_scheduler_start_disabled(mock_settings, scheduler_service):
    """Test that the scheduler doesn't start when disabled"""
    # Configure mock settings
    mock_settings.DISABLE_SCHEDULER = True
    
    # Start scheduler
    scheduler_service.start()
    
    # Check that scheduler was not started
    assert not getattr(scheduler_service.scheduler, "running", False)


@patch('app.services.scheduler_service.settings')
@patch('app.services.scheduler_service.AsyncIOScheduler')
def test_scheduler_start_enabled(mock_scheduler_class, mock_settings, scheduler_service):
    """Test that the scheduler starts when enabled"""
    # Configure mock settings
    mock_settings.DISABLE_SCHEDULER = False
    
    # Configure mock scheduler
    mock_scheduler = MagicMock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Apply mocks to service
    scheduler_service.scheduler = mock_scheduler
    
    # Start scheduler
    scheduler_service.start()
    
    # Check that scheduler was configured correctly
    mock_scheduler.add_job.assert_called_once()
    args, kwargs = mock_scheduler.add_job.call_args
    assert "process_reminders" in kwargs["id"]
    
    # Check that scheduler was started
    mock_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_process_reminders_no_reminders(scheduler_service):
    """Test processing reminders when none are due"""
    # Mock database session
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = []
    
    # Process reminders
    processed = await scheduler_service.process_reminders(mock_session)
    
    # Check result
    assert processed == 0


@pytest.mark.asyncio
@patch('app.services.scheduler_service.logger')
async def test_process_reminders_exception(mock_logger, scheduler_service):
    """Test handling exceptions when processing reminders"""
    # Mock database session to raise an exception
    mock_session = MagicMock()
    mock_session.query().filter().all.side_effect = Exception("Database error")
    
    # Process reminders
    processed = await scheduler_service.process_reminders(mock_session)
    
    # Check result
    assert processed == 0
    
    # Check that error was logged
    mock_logger.error.assert_called_once()
    assert "error processing reminders" in mock_logger.error.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_process_reminders_with_reminders(scheduler_service):
    """Test processing reminders that are due"""
    # Create mock reminders
    mock_reminder1 = MagicMock(spec=Reminder)
    mock_reminder1.id = 1
    mock_reminder1.notification_type = NotificationTypeEnum.EMAIL
    
    mock_reminder2 = MagicMock(spec=Reminder)
    mock_reminder2.id = 2
    mock_reminder2.notification_type = NotificationTypeEnum.SMS
    
    # Mock database session
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = [mock_reminder1, mock_reminder2]
    
    # Mock process_individual_reminder
    with patch.object(scheduler_service, 'process_individual_reminder', new_callable=AsyncMock) as mock_process:
        # Configure the mock to succeed for reminder1 and fail for reminder2
        mock_process.side_effect = [True, False]
        
        # Process reminders
        processed = await scheduler_service.process_reminders(mock_session)
        
        # Check result (only one reminder should be counted as processed)
        assert processed == 1
        
        # Check that process_individual_reminder was called for each reminder
        assert mock_process.call_count == 2
        mock_process.assert_any_call(mock_session, mock_reminder1)
        mock_process.assert_any_call(mock_session, mock_reminder2)


@pytest.mark.asyncio
@patch('app.services.scheduler_service.logger')
async def test_process_individual_reminder_success(mock_logger, scheduler_service):
    """Test successfully processing an individual reminder"""
    # Create mock objects
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.notification_type = NotificationTypeEnum.EMAIL
    mock_reminder.is_recurring = True
    mock_reminder.next_execution = datetime.utcnow() - timedelta(minutes=5)  # 5 minutes ago
    
    mock_user = MagicMock(spec=User)
    mock_user.id = 123
    mock_reminder.user = mock_user
    
    mock_client = MagicMock(spec=Client)
    mock_client.id = 456
    mock_reminder.client = mock_client
    
    # Mock database session
    mock_session = MagicMock(spec=Session)
    
    # Mock send_notification
    with patch.object(scheduler_service, 'send_notification', new_callable=AsyncMock, return_value=True) as mock_send:
        # Mock calculate_next_reminder_date
        with patch.object(scheduler_service, 'calculate_next_reminder_date', return_value=datetime.utcnow() + timedelta(days=1)) as mock_calc:
            # Process reminder
            result = await scheduler_service.process_individual_reminder(mock_session, mock_reminder)
            
            # Check result
            assert result is True
            
            # Check that send_notification was called with correct arguments
            mock_send.assert_called_once_with(
                mock_reminder.notification_type,
                mock_user,
                mock_client,
                mock_reminder,
                None,
                None
            )
            
            # Check that calculate_next_reminder_date was called for recurring reminder
            mock_calc.assert_called_once()
            
            # Check that notification was created
            mock_session.add.assert_called()
            notification = mock_session.add.call_args[0][0]
            assert isinstance(notification, Notification)
            assert notification.reminder_id == mock_reminder.id
            assert notification.status == NotificationStatusEnum.SENT
            
            # Check that reminder was updated
            assert mock_reminder.last_executed == mock_reminder.next_execution
            assert mock_reminder.next_execution > datetime.utcnow()  # Should be future date
            
            # Check that session was committed
            mock_session.commit.assert_called_once()
            
            # Check that success was logged
            mock_logger.info.assert_called()


@pytest.mark.asyncio
@patch('app.services.scheduler_service.logger')
async def test_process_individual_reminder_non_recurring(mock_logger, scheduler_service):
    """Test processing a non-recurring reminder"""
    # Create mock objects
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.notification_type = NotificationTypeEnum.EMAIL
    mock_reminder.is_recurring = False
    mock_reminder.next_execution = datetime.utcnow() - timedelta(minutes=5)  # 5 minutes ago
    
    mock_user = MagicMock(spec=User)
    mock_user.id = 123
    mock_reminder.user = mock_user
    
    mock_client = MagicMock(spec=Client)
    mock_client.id = 456
    mock_reminder.client = mock_client
    
    # Mock database session
    mock_session = MagicMock(spec=Session)
    
    # Mock send_notification
    with patch.object(scheduler_service, 'send_notification', new_callable=AsyncMock, return_value=True) as mock_send:
        # Mock calculate_next_reminder_date
        with patch.object(scheduler_service, 'calculate_next_reminder_date') as mock_calc:
            # Process reminder
            result = await scheduler_service.process_individual_reminder(mock_session, mock_reminder)
            
            # Check result
            assert result is True
            
            # Check that calculate_next_reminder_date was NOT called for non-recurring reminder
            mock_calc.assert_not_called()
            
            # Check that notification was created
            mock_session.add.assert_called()
            
            # Check that reminder was completed (active = False)
            assert mock_reminder.active is False


@pytest.mark.asyncio
@patch('app.services.scheduler_service.logger')
async def test_process_individual_reminder_send_failure(mock_logger, scheduler_service):
    """Test processing a reminder when notification sending fails"""
    # Create mock objects
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.notification_type = NotificationTypeEnum.EMAIL
    mock_reminder.is_recurring = True
    mock_reminder.next_execution = datetime.utcnow() - timedelta(minutes=5)  # 5 minutes ago
    
    mock_user = MagicMock(spec=User)
    mock_user.id = 123
    mock_reminder.user = mock_user
    
    mock_client = MagicMock(spec=Client)
    mock_client.id = 456
    mock_reminder.client = mock_client
    
    # Mock database session
    mock_session = MagicMock(spec=Session)
    
    # Mock send_notification to fail
    with patch.object(scheduler_service, 'send_notification', new_callable=AsyncMock, return_value=False) as mock_send:
        # Process reminder
        result = await scheduler_service.process_individual_reminder(mock_session, mock_reminder)
        
        # Check result
        assert result is False
        
        # Check that notification was created with FAILED status
        mock_session.add.assert_called()
        notification = mock_session.add.call_args[0][0]
        assert notification.status == NotificationStatusEnum.FAILED
        
        # Check that reminder was NOT updated
        assert mock_reminder.last_executed != mock_reminder.next_execution
        
        # Check that session was committed
        mock_session.commit.assert_called_once()
        
        # Check that failure was logged
        mock_logger.error.assert_called()


@pytest.mark.asyncio
@patch('app.services.scheduler_service.EmailService')
async def test_send_notification_email(mock_email_service, scheduler_service):
    """Test sending an email notification"""
    # Create mock objects
    mock_user = MagicMock(spec=User)
    mock_client = MagicMock(spec=Client)
    mock_client.email = "client@example.com"
    
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.description = "Test Description"
    mock_reminder.notification_type = NotificationTypeEnum.EMAIL
    
    mock_email_config = MagicMock()
    mock_sender_identity = MagicMock()
    
    # Configure mock email service
    mock_email_service.send_reminder_email = AsyncMock(return_value=True)
    
    # Send notification
    result = await scheduler_service.send_notification(
        NotificationTypeEnum.EMAIL,
        mock_user,
        mock_client,
        mock_reminder,
        mock_email_config,
        mock_sender_identity
    )
    
    # Check result
    assert result is True
    
    # Check that email service was called with correct arguments
    mock_email_service.send_reminder_email.assert_called_once_with(
        email_configuration=mock_email_config,
        user=mock_user,
        recipient_email=mock_client.email,
        reminder_title=mock_reminder.title,
        reminder_description=mock_reminder.description,
        sender_identity=mock_sender_identity
    )


@pytest.mark.asyncio
@patch('app.services.scheduler_service.EmailService')
async def test_send_notification_email_missing_email(mock_email_service, scheduler_service):
    """Test sending an email notification when client has no email"""
    # Create mock objects
    mock_user = MagicMock(spec=User)
    mock_client = MagicMock(spec=Client)
    mock_client.email = None  # Missing email
    
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.notification_type = NotificationTypeEnum.EMAIL
    
    mock_email_config = MagicMock()
    
    # Mock logger
    with patch('app.services.scheduler_service.logger') as mock_logger:
        # Send notification
        result = await scheduler_service.send_notification(
            NotificationTypeEnum.EMAIL,
            mock_user,
            mock_client,
            mock_reminder,
            mock_email_config
        )
        
        # Check result
        assert result is False
        
        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert "missing email" in mock_logger.warning.call_args[0][0].lower()
        
        # Check that email service was NOT called
        mock_email_service.send_reminder_email.assert_not_called()


@pytest.mark.asyncio
@patch('app.services.scheduler_service.SMSService')
async def test_send_notification_sms(mock_sms_service, scheduler_service):
    """Test sending an SMS notification"""
    # Create mock objects
    mock_user = MagicMock(spec=User)
    mock_client = MagicMock(spec=Client)
    mock_client.phone_number = "+1234567890"
    
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.description = "Test Description"
    mock_reminder.notification_type = NotificationTypeEnum.SMS
    
    # Configure mock SMS service
    mock_sms_service.send_sms = MagicMock(return_value=True)
    
    # Send notification
    result = await scheduler_service.send_notification(
        NotificationTypeEnum.SMS,
        mock_user,
        mock_client,
        mock_reminder
    )
    
    # Check result
    assert result is True
    
    # Check that SMS service was called with correct arguments
    mock_sms_service.send_sms.assert_called_once_with(
        user=mock_user,
        recipient_phone=mock_client.phone_number,
        message=mock_reminder.title,
        track_usage=True
    )


@pytest.mark.asyncio
@patch('app.services.scheduler_service.WhatsAppService')
async def test_send_notification_whatsapp(mock_whatsapp_service, scheduler_service):
    """Test sending a WhatsApp notification"""
    # Create mock objects
    mock_user = MagicMock(spec=User)
    mock_client = MagicMock(spec=Client)
    mock_client.phone_number = "+1234567890"
    
    mock_reminder = MagicMock(spec=Reminder)
    mock_reminder.id = 1
    mock_reminder.title = "Test Reminder"
    mock_reminder.description = "Test Description"
    mock_reminder.notification_type = NotificationTypeEnum.WHATSAPP
    
    # Configure mock WhatsApp service
    mock_whatsapp_service.send_whatsapp = AsyncMock(return_value=True)
    
    # Send notification
    result = await scheduler_service.send_notification(
        NotificationTypeEnum.WHATSAPP,
        mock_user,
        mock_client,
        mock_reminder
    )
    
    # Check result
    assert result is True
    
    # Check that WhatsApp service was called with correct arguments
    mock_whatsapp_service.send_whatsapp.assert_called_once_with(
        service_account=None,
        user=mock_user,
        recipient_phone=mock_client.phone_number,
        message=f"{mock_reminder.title}\n\n{mock_reminder.description}"
    )


def test_calculate_next_reminder_date_daily():
    """Test calculating next date for daily reminder"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 1, 12, 0)  # January 1, 2023, 12:00
    
    # Daily reminder
    next_date = scheduler.calculate_next_reminder_date(current_date, "daily")
    
    # Should be same time, next day
    assert next_date.year == 2023
    assert next_date.month == 1
    assert next_date.day == 2
    assert next_date.hour == 12
    assert next_date.minute == 0


def test_calculate_next_reminder_date_weekly():
    """Test calculating next date for weekly reminder"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 1, 12, 0)  # January 1, 2023, 12:00 (Sunday)
    
    # Weekly reminder
    next_date = scheduler.calculate_next_reminder_date(current_date, "weekly")
    
    # Should be same time, next week
    assert next_date.year == 2023
    assert next_date.month == 1
    assert next_date.day == 8  # Next Sunday
    assert next_date.hour == 12
    assert next_date.minute == 0


def test_calculate_next_reminder_date_monthly():
    """Test calculating next date for monthly reminder"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 15, 12, 0)  # January 15, 2023, 12:00
    
    # Monthly reminder
    next_date = scheduler.calculate_next_reminder_date(current_date, "monthly")
    
    # Should be same day of month, next month
    assert next_date.year == 2023
    assert next_date.month == 2
    assert next_date.day == 15
    assert next_date.hour == 12
    assert next_date.minute == 0


def test_calculate_next_reminder_date_quarterly():
    """Test calculating next date for quarterly reminder"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 15, 12, 0)  # January 15, 2023, 12:00
    
    # Quarterly reminder
    next_date = scheduler.calculate_next_reminder_date(current_date, "quarterly")
    
    # Should be 3 months later
    assert next_date.year == 2023
    assert next_date.month == 4  # April
    assert next_date.day == 15
    assert next_date.hour == 12
    assert next_date.minute == 0


def test_calculate_next_reminder_date_yearly():
    """Test calculating next date for yearly reminder"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 15, 12, 0)  # January 15, 2023, 12:00
    
    # Yearly reminder
    next_date = scheduler.calculate_next_reminder_date(current_date, "yearly")
    
    # Should be same day, next year
    assert next_date.year == 2024
    assert next_date.month == 1
    assert next_date.day == 15
    assert next_date.hour == 12
    assert next_date.minute == 0


def test_calculate_next_reminder_date_invalid():
    """Test calculating next date for invalid pattern"""
    scheduler = SchedulerService()
    current_date = datetime(2023, 1, 15, 12, 0)
    
    # Invalid pattern
    next_date = scheduler.calculate_next_reminder_date(current_date, "invalid_pattern")
    
    # Should return None for invalid pattern
    assert next_date is None 