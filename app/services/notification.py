from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.notification import notification_repository
from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.models.notifications import Notification, NotificationStatusEnum
from app.schemas.notifications import (
    NotificationCreate, 
    NotificationUpdate, 
    Notification as NotificationSchema,
    NotificationDetail
)
from app.core.exceptions import (
    NotificationNotFoundError,
    ReminderNotFoundError,
    ClientNotFoundError,
    UserNotFoundError,
    InvalidConfigurationError
)

class NotificationService:
    """
    Service layer for Notification operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = notification_repository
        self.reminder_repository = reminder_repository
        self.client_repository = client_repository
    
    def get_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Get a notification by ID.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Notification object
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.repository.get(db, id=notification_id)
        if not notification:
            raise NotificationNotFoundError(
                f"Notification with ID {notification_id} not found"
            )
        return notification
    
    def get_notification_detail(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> NotificationDetail:
        """
        Get a notification with extra details.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            NotificationDetail: Notification with extra details
            
        Raises:
            NotificationNotFoundError: If notification not found
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        
        # Get reminder details
        reminder = self.reminder_repository.get(db, id=notification.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(
                f"Reminder with ID {notification.reminder_id} not found"
            )
            
        # Get client details
        client = self.client_repository.get(db, id=notification.client_id)
        if not client:
            raise ClientNotFoundError(
                f"Client with ID {notification.client_id} not found"
            )
        
        # Create NotificationDetail object
        notification_data = NotificationSchema.model_validate(notification).model_dump()
        return NotificationDetail(
            **notification_data,
            reminder_title=reminder.title,
            client_name=client.name
        )
    
    def get_reminder_notifications(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_reminder_id(
            db,
            reminder_id=reminder_id,
            skip=skip,
            limit=limit
        )
    
    def get_client_notifications(
        self, 
        db: Session, 
        *, 
        client_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_client_id(
            db,
            client_id=client_id,
            skip=skip,
            limit=limit
        )
    
    def get_notifications_by_status(
        self, 
        db: Session, 
        *, 
        status: NotificationStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications with a specific status.
        
        Args:
            db: Database session
            status: Notification status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_status(
            db,
            status=status,
            skip=skip,
            limit=limit
        )
    
    def get_notifications_by_type(
        self, 
        db: Session, 
        *, 
        notification_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications of a specific type.
        
        Args:
            db: Database session
            notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_type(
            db,
            notification_type=notification_type,
            skip=skip,
            limit=limit
        )
    
    def get_pending_notifications(
        self, 
        db: Session, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all pending notifications.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of pending notifications
        """
        return self.repository.get_pending_notifications(
            db,
            skip=skip,
            limit=limit
        )
    
    def get_failed_notifications(
        self, 
        db: Session, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all failed notifications.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of failed notifications
        """
        return self.repository.get_failed_notifications(
            db,
            skip=skip,
            limit=limit
        )
    
    def create_notification(
        self, 
        db: Session, 
        *, 
        notification_in: NotificationCreate
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            db: Database session
            notification_in: Notification creation data
            
        Returns:
            Notification: Created notification
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        # Validate reminder exists
        reminder = self.reminder_repository.get(db, id=notification_in.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(
                f"Reminder with ID {notification_in.reminder_id} not found"
            )
            
        # Validate client exists
        client = self.client_repository.get(db, id=notification_in.client_id)
        if not client:
            raise ClientNotFoundError(
                f"Client with ID {notification_in.client_id} not found"
            )
        
        return self.repository.create(db, obj_in=notification_in)
    
    def update_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        notification_in: NotificationUpdate | Dict[str, Any]
    ) -> Notification:
        """
        Update a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            notification_in: Update data
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.update(db, db_obj=notification, obj_in=notification_in)
    
    def delete_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Delete a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Deleted notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.delete(db, id=notification_id)
    
    def mark_as_sent(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Mark a notification as sent.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_sent(db, notification_id=notification_id)
    
    def mark_as_failed(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        error_message: str
    ) -> Notification:
        """
        Mark a notification as failed.
        
        Args:
            db: Database session
            notification_id: Notification ID
            error_message: Error message
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_failed(
            db,
            notification_id=notification_id,
            error_message=error_message
        )
    
    def mark_as_cancelled(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Mark a notification as cancelled.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_cancelled(db, notification_id=notification_id)
    
    async def create_and_send_notifications_for_reminder(self, db: Session, *, reminder) -> None:
        """
        Create and send notifications for a specific reminder.
        
        Args:
            db: Database session
            reminder: Reminder object
            
        Returns:
            None
            
        Raises:
            UserNotFoundError: If user not found or inactive
            InvalidConfigurationError: If required configuration is missing
        """
        from app.services.scheduler_service import scheduler_service
        from app.models.users import User
        from app.models.emailConfigurations import EmailConfiguration
        from app.models.senderIdentities import SenderIdentity
        from app.models.clients import Client
        from app.models.reminderRecipient import ReminderRecipient
        from app.models.notifications import Notification, NotificationStatusEnum
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get the user who created the reminder
        user = db.query(User).filter(User.id == reminder.user_id).first()
        if not user or not user.is_active:
            raise UserNotFoundError(f"User {reminder.user_id} not found or inactive")
        
        # For email reminders, ensure we have a valid email configuration
        email_configuration = None
        if reminder.notification_type == "EMAIL":
            if reminder.email_configuration_id:
                email_configuration = db.query(EmailConfiguration).filter(
                    EmailConfiguration.id == reminder.email_configuration_id,
                    EmailConfiguration.user_id == user.id,
                    EmailConfiguration.is_active == True
                ).first()
            
            if not email_configuration:
                raise InvalidConfigurationError("No active email configuration found")
        
        # Get sender identity if specified
        sender_identity = None
        if reminder.sender_identity_id:
            sender_identity = db.query(SenderIdentity).filter(
                SenderIdentity.id == reminder.sender_identity_id,
                SenderIdentity.user_id == user.id
            ).first()
        
        # Get all clients for this reminder
        recipient_mappings = (
            db.query(ReminderRecipient)
            .filter(ReminderRecipient.reminder_id == reminder.id)
            .all()
        )
        
        client_ids = [mapping.client_id for mapping in recipient_mappings]
        clients = db.query(Client).filter(Client.id.in_(client_ids), Client.is_active == True).all()
        
        if not clients:
            logger.warning(f"No active clients found for reminder {reminder.id}")
            return
        
        # Process each client
        for client in clients:
            # Check if a notification already exists
            existing_notification = (
                db.query(Notification)
                .filter(
                    Notification.reminder_id == reminder.id,
                    Notification.client_id == client.id,
                    Notification.status.in_([NotificationStatusEnum.PENDING, NotificationStatusEnum.SENT])
                )
                .first()
            )
            
            # Skip if already processed
            if existing_notification and existing_notification.status == NotificationStatusEnum.SENT:
                continue
            
            # Create a new notification if one doesn't exist
            if not existing_notification:
                notification = Notification(
                    user_id=reminder.user_id,
                    reminder_id=reminder.id,
                    client_id=client.id,
                    notification_type=reminder.notification_type,
                    message=reminder.description,
                    status=NotificationStatusEnum.PENDING
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
            else:
                notification = existing_notification
            
            # Send the notification
            success = await scheduler_service.send_notification(
                notification_type=reminder.notification_type,
                email_configuration=email_configuration,
                sender_identity=sender_identity,
                user=user,
                client=client,
                reminder=reminder
            )
            
            # Update notification status
            notification.sent_at = datetime.now()
            if success:
                notification.status = NotificationStatusEnum.SENT
                logger.info(f"Successfully sent notification {notification.id} for reminder {reminder.id} to client {client.id}")
            else:
                notification.status = NotificationStatusEnum.FAILED
                notification.error_message = "Failed to send notification"
                logger.error(f"Failed to send notification {notification.id} for reminder {reminder.id} to client {client.id}")
            
            db.add(notification)
        
        db.commit()
    
    def resend_notification(self, db: Session, *, notification_id: int, user_id: int) -> None:
        """
        Resend a failed notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID for permission check
            
        Returns:
            None
            
        Raises:
            NotificationNotFoundError: If notification not found
            InvalidOperationError: If notification is not in FAILED status
        """
        from app.models.reminders import Reminder
        
        # Get notification
        notification = self.get_notification(db, notification_id=notification_id)
        
        # Get reminder
        reminder = self.reminder_repository.get(db, id=notification.reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {notification.reminder_id} not found or access denied")
        
        # Reset notification status to PENDING
        notification.status = NotificationStatusEnum.PENDING
        notification.error_message = None
        db.add(notification)
        db.commit()
        
        # Create and send notification
        self.create_and_send_notifications_for_reminder(db, reminder=reminder)
    
    def get_notifications(
        self, 
        db: Session, 
        *,
        user_id: int,  # Required for permission checking
        skip: int = 0,
        limit: int = 100,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        status: Optional[NotificationStatusEnum] = None
    ) -> List[Notification]:
        """
        Get notifications with optional filtering.
        All notifications returned will belong to the specified user.
        
        Args:
            db: Database session
            user_id: User ID for filtering and permission check
            skip: Number of records to skip
            limit: Maximum number of records to return
            reminder_id: Optional reminder ID filter
            client_id: Optional client ID filter
            status: Optional status filter
            
        Returns:
            List[Notification]: List of notifications
        """
        # Build query with user_id filter
        query = db.query(self.repository.model).filter(
            self.repository.model.user_id == user_id
        )
        
        # Add optional filters
        if reminder_id is not None:
            query = query.filter(self.repository.model.reminder_id == reminder_id)
        
        if client_id is not None:
            query = query.filter(self.repository.model.client_id == client_id)
        
        if status is not None:
            query = query.filter(self.repository.model.status == status)
        
        # Return paginated results
        return query.offset(skip).limit(limit).all()
    
    def get_user_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_user_id(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    
    def get_user_notifications_by_status(
        self, 
        db: Session, 
        *, 
        user_id: int,
        status: NotificationStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a user with a specific status.
        
        Args:
            db: Database session
            user_id: User ID
            status: Notification status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_user_id_and_status(
            db,
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit
        )

# Create singleton instance
notification_service = NotificationService() 