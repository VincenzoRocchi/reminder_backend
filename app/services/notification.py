from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.repositories.notification import notification_repository
from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.models.notifications import Notification, NotificationStatusEnum
from app.schemas.notifications import (
    NotificationCreate, 
    NotificationUpdate, 
    NotificationSchema,
    NotificationDetail
)
from app.core.exceptions import (
    NotificationNotFoundError,
    ReminderNotFoundError,
    ClientNotFoundError,
    UserNotFoundError,
    InvalidConfigurationError,
    InvalidOperationError
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
    
    def get_all_notifications(
        self, 
        db: Session, 
        *,
        skip: int = 0,
        limit: int = 100,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[NotificationStatusEnum] = None
    ) -> List[Notification]:
        """
        Get all notifications across users with optional filtering.
        For admin/superuser use only.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            reminder_id: Optional reminder ID filter
            client_id: Optional client ID filter
            user_id: Optional user ID filter
            status: Optional status filter
            
        Returns:
            List[Notification]: List of notifications
        """
        # Build base query
        query = db.query(self.repository.model)
        
        # Add optional filters
        if reminder_id is not None:
            query = query.filter(self.repository.model.reminder_id == reminder_id)
        
        if client_id is not None:
            query = query.filter(self.repository.model.client_id == client_id)
            
        if user_id is not None:
            query = query.filter(self.repository.model.user_id == user_id)
        
        if status is not None:
            query = query.filter(self.repository.model.status == status)
        
        # Return paginated results
        return query.order_by(self.repository.model.created_at.desc()).offset(skip).limit(limit).all()
    
    def generate_notifications_for_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: int
    ) -> List[Notification]:
        """
        Generate notifications for a reminder without sending them.
        
        This method creates pending notifications for all clients associated with the reminder,
        but does not attempt to actually send them. This is useful for preparing notifications
        that will be sent later by a scheduled job or manually by the user.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID for permission check
            
        Returns:
            List[Notification]: List of created notifications
            
        Raises:
            ReminderNotFoundError: If reminder not found or doesn't belong to user
            InvalidOperationError: If no active clients found for the reminder
        """
        from app.models.reminderRecipient import ReminderRecipient
        from app.models.clients import Client
        
        # Validate reminder exists and belongs to user
        reminder = self.reminder_repository.get(db, id=reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
        
        # Get all clients for this reminder
        recipient_mappings = (
            db.query(ReminderRecipient)
            .filter(ReminderRecipient.reminder_id == reminder_id)
            .all()
        )
        
        if not recipient_mappings:
            raise InvalidOperationError("No clients associated with this reminder")
        
        client_ids = [mapping.client_id for mapping in recipient_mappings]
        clients = db.query(Client).filter(
            Client.id.in_(client_ids), 
            Client.is_active == True
        ).all()
        
        if not clients:
            raise InvalidOperationError("No active clients found for this reminder")
        
        # Create notifications for each client
        created_notifications = []
        for client in clients:
            # Check if notification already exists
            existing = db.query(Notification).filter(
                Notification.reminder_id == reminder_id,
                Notification.client_id == client.id
            ).first()
            
            # Skip if notification already exists
            if existing:
                created_notifications.append(existing)
                continue
            
            # Create new notification
            notification = Notification(
                user_id=user_id,
                reminder_id=reminder_id,
                client_id=client.id,
                notification_type=reminder.notification_type,
                message=reminder.description,
                status=NotificationStatusEnum.PENDING
            )
            db.add(notification)
            db.flush()  # Get ID without committing transaction
            created_notifications.append(notification)
        
        # Commit all new notifications
        db.commit()
        
        # Refresh all notifications
        for notification in created_notifications:
            db.refresh(notification)
            
        return created_notifications
    
    def batch_cancel_pending_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        limit: int = 100
    ) -> int:
        """
        Cancel multiple pending notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            reminder_id: Optional reminder ID filter
            client_id: Optional client ID filter
            limit: Maximum number of notifications to cancel
            
        Returns:
            int: Number of notifications cancelled
        """
        # Build query for pending notifications for this user
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatusEnum.PENDING
        )
        
        # Add optional filters
        if reminder_id is not None:
            query = query.filter(Notification.reminder_id == reminder_id)
            
        if client_id is not None:
            query = query.filter(Notification.client_id == client_id)
        
        # Limit the results
        pending_notifications = query.limit(limit).all()
        
        # Update status to CANCELLED for each notification
        count = 0
        for notification in pending_notifications:
            notification.status = NotificationStatusEnum.CANCELLED
            db.add(notification)
            count += 1
        
        db.commit()
        
        # Return the count of notifications cancelled
        return count
    
    def batch_delete_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        status: Optional[NotificationStatusEnum] = None,
        limit: int = 50
    ) -> int:
        """
        Delete multiple notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            reminder_id: Optional reminder ID filter
            client_id: Optional client ID filter
            status: Optional status filter
            limit: Maximum number of notifications to delete
            
        Returns:
            int: Number of notifications deleted
        """
        # Build query for notifications for this user
        query = db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        # Add optional filters
        if reminder_id is not None:
            query = query.filter(Notification.reminder_id == reminder_id)
            
        if client_id is not None:
            query = query.filter(Notification.client_id == client_id)
            
        if status is not None:
            query = query.filter(Notification.status == status)
        
        # Get notifications to delete
        notifications_to_delete = query.limit(limit).all()
        
        # Delete each notification
        count = 0
        for notification in notifications_to_delete:
            db.delete(notification)
            count += 1
        
        db.commit()
        
        # Return the count of notifications deleted
        return count
    
    def get_user_notification_counts(
        self, 
        db: Session, 
        *, 
        user_id: int
    ) -> Dict[str, int]:
        """
        Get counts of notifications by status for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict[str, int]: Counts by status and total
        """
        from sqlalchemy import func
        
        # Base query for this user's notifications
        base_query = db.query(
            Notification.status, 
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.status)
        
        # Execute the query
        results = base_query.all()
        
        # Organize results into a dictionary
        counts = {
            "total": 0,
            "pending": 0,
            "sent": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for status, count in results:
            status_key = status.value.lower()
            counts[status_key] = count
            counts["total"] += count
        
        return counts
    
    def filter_notifications(
        self, 
        db: Session, 
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        notification_type: Optional[str] = None,
        status: Optional[NotificationStatusEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Notification]:
        """
        Advanced filtering of notifications with multiple parameters.
        
        Args:
            db: Database session
            user_id: User ID for permission check
            skip: Number of records to skip
            limit: Maximum number of records to return
            reminder_id: Optional reminder ID filter
            client_id: Optional client ID filter
            notification_type: Optional notification type filter
            status: Optional status filter
            start_date: Optional start date filter (created after this date)
            end_date: Optional end date filter (created before this date)
            
        Returns:
            List[Notification]: List of notifications matching filters
        """
        # Build base query with user_id filter for security
        query = db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        # Add optional filters
        if reminder_id is not None:
            query = query.filter(Notification.reminder_id == reminder_id)
        
        if client_id is not None:
            query = query.filter(Notification.client_id == client_id)
            
        if notification_type is not None:
            query = query.filter(Notification.notification_type == notification_type)
            
        if status is not None:
            query = query.filter(Notification.status == status)
            
        if start_date is not None:
            query = query.filter(Notification.created_at >= start_date)
            
        if end_date is not None:
            query = query.filter(Notification.created_at <= end_date)
        
        # Return paginated results ordered by most recent first
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_notification_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get global notification statistics.
        For admin/superuser use only.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, Any]: Statistics about notifications
        """
        from sqlalchemy import func
        
        # Total counts
        total_count = db.query(func.count(Notification.id)).scalar()
        
        # Count by status
        status_counts = db.query(
            Notification.status,
            func.count(Notification.id).label('count')
        ).group_by(Notification.status).all()
        
        status_dict = {status.value.lower(): 0 for status in NotificationStatusEnum}
        for status, count in status_counts:
            status_dict[status.value.lower()] = count
            
        # Count by type
        type_counts = db.query(
            Notification.notification_type,
            func.count(Notification.id).label('count')
        ).group_by(Notification.notification_type).all()
        
        type_dict = {}
        for ntype, count in type_counts:
            type_dict[ntype.lower() if isinstance(ntype, str) else ntype.value.lower()] = count
            
        # Calculate delivery rates
        delivery_rate = 0
        if (status_dict['sent'] + status_dict['failed']) > 0:
            delivery_rate = (status_dict['sent'] / (status_dict['sent'] + status_dict['failed'])) * 100
            
        # Get recent failed count (last 24 hours)
        recent_failed_count = db.query(func.count(Notification.id)).filter(
            Notification.status == NotificationStatusEnum.FAILED,
            Notification.created_at >= datetime.now() - timedelta(days=1)
        ).scalar()
        
        # Get user counts
        user_counts = db.query(
            Notification.user_id,
            func.count(Notification.id).label('count')
        ).group_by(Notification.user_id).all()
        
        return {
            "total_count": total_count,
            "by_status": status_dict,
            "by_type": type_dict,
            "delivery_rate_percent": round(delivery_rate, 2),
            "recent_failed_count": recent_failed_count,
            "user_count": len(user_counts),
            "generated_at": datetime.now().isoformat()
        }
        
    def clear_old_failed_notifications(
        self, 
        db: Session, 
        *, 
        older_than_days: int = 7,
        limit: int = 1000
    ) -> int:
        """
        Delete old failed notifications to clean up the database.
        For admin/superuser use only.
        
        Args:
            db: Database session
            older_than_days: Delete notifications older than this many days
            limit: Maximum number of notifications to delete
            
        Returns:
            int: Number of notifications deleted
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Find old failed notifications
        old_failed_notifications = db.query(Notification).filter(
            Notification.status == NotificationStatusEnum.FAILED,
            Notification.created_at < cutoff_date
        ).limit(limit).all()
        
        # Delete each notification
        count = 0
        for notification in old_failed_notifications:
            db.delete(notification)
            count += 1
        
        db.commit()
        
        return count
        
    def resend_all_failed_notifications(
        self, 
        db: Session, 
        *, 
        limit: int = 100
    ) -> int:
        """
        Reset all failed notifications to pending status for resending.
        For admin/superuser use only.
        
        Args:
            db: Database session
            limit: Maximum number of notifications to reset
            
        Returns:
            int: Number of notifications reset for resending
        """
        # Find failed notifications
        failed_notifications = db.query(Notification).filter(
            Notification.status == NotificationStatusEnum.FAILED
        ).limit(limit).all()
        
        # Reset status to PENDING for each notification
        count = 0
        for notification in failed_notifications:
            notification.status = NotificationStatusEnum.PENDING
            notification.error_message = None
            db.add(notification)
            count += 1
        
        db.commit()
        
        return count

    def get_detailed_user_notifications(
        self, 
        db: Session, 
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[NotificationStatusEnum] = None
    ) -> List[NotificationDetail]:
        """
        Get detailed notifications for a user with client and reminder details.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List[NotificationDetail]: List of detailed notifications
        """
        # Get basic notifications first
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if status is not None:
            query = query.filter(Notification.status == status)
            
        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to detailed notifications
        detailed_notifications = []
        for notification in notifications:
            # Get reminder details
            reminder = self.reminder_repository.get(db, id=notification.reminder_id)
            if not reminder:
                continue
                
            # Get client details
            client = self.client_repository.get(db, id=notification.client_id)
            if not client:
                continue
                
            # Create detailed notification
            notification_data = NotificationSchema.model_validate(notification).model_dump()
            detailed_notification = NotificationDetail(
                **notification_data,
                reminder_title=reminder.title,
                client_name=client.name
            )
            detailed_notifications.append(detailed_notification)
            
        return detailed_notifications

# Create singleton instance
notification_service = NotificationService() 