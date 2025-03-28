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
    InvalidOperationError,
    ServiceError
)
from app.core.error_handling import handle_exceptions, with_transaction

class NotificationService:
    """
    Service layer for Notification operations.
    Handles business logic and uses the repository for data access.
    
    Notifications are created as part of the reminder system:
    1. When a reminder is triggered (create_and_send_notifications_for_reminder)
    2. When notifications are pre-generated for a reminder (generate_notifications_for_reminder)
    """
    
    def __init__(self):
        self.repository = notification_repository
        self.reminder_repository = reminder_repository
        self.client_repository = client_repository
    
    @handle_exceptions(error_message="Failed to get notification")
    def get_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int, 
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Get a notification by ID.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Notification object
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.repository.get(db, id=notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification with ID {notification_id} not found")
            
        # If user_id is provided, verify ownership
        if user_id and notification.reminder.user_id != user_id:
            raise NotificationNotFoundError(f"Notification with ID {notification_id} not found")
            
        return notification
    
    @handle_exceptions(error_message="Failed to get notification detail")
    def get_notification_detail(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        user_id: Optional[int] = None
    ) -> NotificationDetail:
        """
        Get a notification with extra details.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: Optional user ID for authorization
            
        Returns:
            NotificationDetail: Notification with extra details
            
        Raises:
            NotificationNotFoundError: If notification not found
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        
        # Get reminder details
        reminder = self.reminder_repository.get(db, id=notification.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {notification.reminder_id} not found")
            
        # Get client details
        client = self.client_repository.get(db, id=notification.client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {notification.client_id} not found")
        
        # Create NotificationDetail object
        notification_data = NotificationSchema.model_validate(notification).model_dump()
        return NotificationDetail(
            **notification_data,
            reminder_title=reminder.title,
            client_name=client.name
        )
    
    @handle_exceptions(error_message="Failed to get notifications by reminder")
    def get_notifications_by_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: Optional user ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        # Verify reminder exists
        reminder = self.reminder_repository.get(db, id=reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            
        # If user_id is provided, verify ownership
        if user_id and reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            
        return self.repository.get_by_reminder_id(
            db, reminder_id=reminder_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get notifications by client")
    def get_notifications_by_client(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: Optional user ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
            
        Raises:
            ClientNotFoundError: If client not found
        """
        # Verify client exists
        client = self.client_repository.get(db, id=client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
            
        # If user_id is provided, verify ownership
        if user_id and client.user_id != user_id:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
            
        return self.repository.get_by_client_id(
            db, client_id=client_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get notifications by user")
    def get_notifications_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[NotificationStatusEnum] = None
    ) -> List[Notification]:
        """
        Get all notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List[Notification]: List of notifications
        """
        # Get notifications through reminders owned by the user
        query_params = {"user_id": user_id, "skip": skip, "limit": limit}
        if status:
            query_params["status"] = status
            
        return self.repository.get_filtered(db, **query_params)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create notification")
    def create_notification(
        self, 
        db: Session, 
        *, 
        obj_in: NotificationCreate
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            db: Database session
            obj_in: Notification creation schema
            
        Returns:
            Notification: Created notification
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        # Verify reminder exists
        reminder = self.reminder_repository.get(db, id=obj_in.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {obj_in.reminder_id} not found")
            
        # Verify client exists
        client = self.client_repository.get(db, id=obj_in.client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {obj_in.client_id} not found")
            
        # Verify reminder and client belong to the same user
        if reminder.user_id != client.user_id:
            raise InvalidOperationError("Reminder and client must belong to the same user")
            
        return self.repository.create(db, obj_in=obj_in)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update notification")
    def update_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        obj_in: NotificationUpdate,
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Update a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            obj_in: Notification update schema
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        return self.repository.update(db, db_obj=notification, obj_in=obj_in)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete notification")
    def delete_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Delete a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Deleted notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        return self.repository.delete(db, id=notification_id)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark notification as sent")
    def mark_as_sent(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Mark a notification as sent.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        return self.repository.mark_as_sent(db, notification_id=notification_id)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark notification as failed")
    def mark_as_failed(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        error_message: str,
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Mark a notification as failed.
        
        Args:
            db: Database session
            notification_id: Notification ID
            error_message: Error message describing the failure
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        return self.repository.mark_as_failed(db, notification_id=notification_id, error_message=error_message)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark notification as cancelled")
    def mark_as_cancelled(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        user_id: Optional[int] = None
    ) -> Notification:
        """
        Mark a notification as cancelled.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: Optional user ID for authorization
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        return self.repository.mark_as_cancelled(db, notification_id=notification_id)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create and send notifications for reminder")
    def create_and_send_notifications_for_reminder(
        self, 
        db: Session, 
        *, 
        reminder
    ) -> List[Notification]:
        """
        Create and send notifications for a reminder to all associated clients.
        
        Args:
            db: Database session
            reminder: Reminder object
            
        Returns:
            List[Notification]: List of created notifications
            
        Raises:
            InvalidConfigurationError: If notification configuration is invalid
            ServiceError: If notification sending fails
        """
        # Import here to avoid circular imports
        from app.services.scheduler_service import scheduler_service
        
        created_notifications = []
        
        # Get all clients associated with this reminder
        clients = [rr.client for rr in reminder.reminder_recipients]
        
        for client in clients:
            # Create notification record
            notification_data = NotificationCreate(
                reminder_id=reminder.id,
                client_id=client.id,
                notification_type=reminder.notification_type,
                status=NotificationStatusEnum.PENDING,
                scheduled_time=datetime.utcnow()
            )
            
            notification = self.repository.create(db, obj_in=notification_data)
            created_notifications.append(notification)
            
            try:
                # Attempt to send the notification
                sent = scheduler_service.send_notification(
                    notification_type=reminder.notification_type,
                    user=reminder.user,
                    client=client,
                    reminder=reminder,
                    email_configuration=reminder.email_configuration,
                    sender_identity=reminder.sender_identity
                )
                
                # Update notification status based on result
                if sent:
                    self.repository.mark_as_sent(db, notification_id=notification.id)
                else:
                    self.repository.mark_as_failed(
                        db, 
                        notification_id=notification.id, 
                        error_message="Failed to send notification"
                    )
                    
            except Exception as e:
                # Log and record the error
                self.repository.mark_as_failed(
                    db, 
                    notification_id=notification.id, 
                    error_message=str(e)
                )
                
        return created_notifications

    @handle_exceptions(error_message="Failed to get notification statistics")
    def get_notification_statistics(
        self, 
        db: Session, 
        *, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get notification statistics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dict[str, Any]: Dictionary with statistics
        """
        # Define filters
        filters = {"user_id": user_id}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
            
        # Get total counts
        total_count = self.repository.count(db, filters=filters)
        
        # Add status filter for each status type
        sent_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.SENT})
        failed_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.FAILED})
        pending_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.PENDING})
        cancelled_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.CANCELLED})
        
        # Calculate success rate
        success_rate = (sent_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "total_count": total_count,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "cancelled_count": cancelled_count,
            "success_rate": success_rate
        }
    
    @handle_exceptions(error_message="Failed to get failed notifications")
    def get_failed_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all failed notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of failed notifications
        """
        return self.repository.get_failed_notifications(
            db, user_id=user_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get notifications by status")
    def get_notifications_by_status(
        self, 
        db: Session, 
        *, 
        status: NotificationStatusEnum,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications with a specific status.
        
        Args:
            db: Database session
            status: Notification status
            user_id: Optional user ID for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_status(
            db, status=status, user_id=user_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get recent notifications")
    def get_recent_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get recent notifications for a user within the specified number of days.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of recent notifications
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return self.repository.get_filtered(
            db, 
            user_id=user_id,
            start_date=start_date,
            skip=skip,
            limit=limit
        )

    @with_transaction
    @handle_exceptions(error_message="Failed to resend notification")
    def resend_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int, 
        user_id: int
    ) -> Notification:
        """
        Resend a failed notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID for authorization
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
            InvalidOperationError: If notification is not in FAILED status
        """
        # Import here to avoid circular imports
        from app.services.scheduler_service import scheduler_service
        
        # Get notification
        notification = self.get_notification(db, notification_id=notification_id, user_id=user_id)
        
        # Verify notification is in FAILED status
        if notification.status != NotificationStatusEnum.FAILED:
            raise InvalidOperationError("Only failed notifications can be resent")
        
        # Get reminder
        reminder = self.reminder_repository.get(db, id=notification.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {notification.reminder_id} not found")
        
        # Get client
        client = self.client_repository.get(db, id=notification.client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {notification.client_id} not found")
        
        # Reset notification status to PENDING
        notification = self.repository.update(
            db, 
            db_obj=notification, 
            obj_in={"status": NotificationStatusEnum.PENDING, "error_message": None}
        )
        
        try:
            # Attempt to send the notification
            sent = scheduler_service.send_notification(
                notification_type=reminder.notification_type,
                user=reminder.user,
                client=client,
                reminder=reminder,
                email_configuration=reminder.email_configuration,
                sender_identity=reminder.sender_identity
            )
            
            # Update notification status based on result
            if sent:
                notification = self.repository.mark_as_sent(db, notification_id=notification.id)
            else:
                notification = self.repository.mark_as_failed(
                    db, 
                    notification_id=notification.id, 
                    error_message="Failed to send notification"
                )
                
        except Exception as e:
            # Log and record the error
            notification = self.repository.mark_as_failed(
                db, 
                notification_id=notification.id, 
                error_message=str(e)
            )
            
        return notification

    @with_transaction
    @handle_exceptions(error_message="Failed to generate notifications for reminder")
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
            user_id: User ID for authorization
            
        Returns:
            List[Notification]: List of created notifications
            
        Raises:
            ReminderNotFoundError: If reminder not found or doesn't belong to user
            InvalidOperationError: If no active clients found for the reminder
        """
        # Validate reminder exists and belongs to user
        reminder = self.reminder_repository.get(db, id=reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
        
        # Get all client recipients for this reminder
        clients = [rr.client for rr in reminder.reminder_recipients if rr.client.is_active]
        
        if not clients:
            raise InvalidOperationError("No active clients found for this reminder")
        
        # Create notifications for each client
        created_notifications = []
        for client in clients:
            # Check if notification already exists
            existing = self.repository.get_filtered(
                db,
                reminder_id=reminder_id,
                client_id=client.id,
                limit=1
            )
            
            # Skip if notification already exists
            if existing:
                created_notifications.append(existing[0])
                continue
            
            # Create new notification
            notification_data = NotificationCreate(
                reminder_id=reminder_id,
                client_id=client.id,
                notification_type=reminder.notification_type,
                status=NotificationStatusEnum.PENDING,
                scheduled_time=datetime.utcnow()
            )
            
            notification = self.repository.create(db, obj_in=notification_data)
            created_notifications.append(notification)
            
        return created_notifications
    
    @with_transaction
    @handle_exceptions(error_message="Failed to cancel pending notifications")
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
        # Build filter parameters
        filters = {
            "user_id": user_id,
            "status": NotificationStatusEnum.PENDING,
            "limit": limit
        }
        
        if reminder_id is not None:
            # Verify reminder exists and belongs to user
            reminder = self.reminder_repository.get(db, id=reminder_id)
            if not reminder or reminder.user_id != user_id:
                raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            filters["reminder_id"] = reminder_id
            
        if client_id is not None:
            # Verify client exists and belongs to user
            client = self.client_repository.get(db, id=client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {client_id} not found")
            filters["client_id"] = client_id
            
        # Get pending notifications
        pending_notifications = self.repository.get_filtered(db, **filters)
        
        # Update status to CANCELLED for each notification
        count = 0
        for notification in pending_notifications:
            self.repository.mark_as_cancelled(db, notification_id=notification.id)
            count += 1
        
        return count
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete notifications")
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
        # Build filter parameters
        filters = {
            "user_id": user_id,
            "limit": limit
        }
        
        if reminder_id is not None:
            # Verify reminder exists and belongs to user
            reminder = self.reminder_repository.get(db, id=reminder_id)
            if not reminder or reminder.user_id != user_id:
                raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            filters["reminder_id"] = reminder_id
            
        if client_id is not None:
            # Verify client exists and belongs to user
            client = self.client_repository.get(db, id=client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {client_id} not found")
            filters["client_id"] = client_id
            
        if status is not None:
            filters["status"] = status
        
        # Get notifications to delete
        notifications_to_delete = self.repository.get_filtered(db, **filters)
        
        # Delete each notification
        count = 0
        for notification in notifications_to_delete:
            self.repository.delete(db, id=notification.id)
            count += 1
        
        return count
    
    @handle_exceptions(error_message="Failed to get user notification counts")
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
        # Define base filters
        filters = {"user_id": user_id}
        
        # Get total count
        total_count = self.repository.count(db, filters=filters)
        
        # Get count for each status
        pending_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.PENDING})
        sent_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.SENT})
        failed_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.FAILED})
        cancelled_count = self.repository.count(
            db, filters={**filters, "status": NotificationStatusEnum.CANCELLED})
        
        return {
            "total": total_count,
            "pending": pending_count,
            "sent": sent_count,
            "failed": failed_count,
            "cancelled": cancelled_count
        }
    
    @handle_exceptions(error_message="Failed to get detailed notifications")
    def get_detailed_user_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        status: Optional[NotificationStatusEnum] = None,
        notification_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[NotificationDetail]:
        """
        Get detailed notifications for a user with flexible filtering options.
        
        Args:
            db: Database session
            user_id: User ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            reminder_id: Filter by reminder ID
            client_id: Filter by client ID
            status: Filter by notification status
            notification_type: Filter by notification type
            start_date: Filter by notifications created after this date
            end_date: Filter by notifications created before this date
            
        Returns:
            List[NotificationDetail]: List of notifications with details
        """
        # Build filter parameters
        filters = {
            "user_id": user_id,
            "skip": skip,
            "limit": limit
        }
        
        if reminder_id is not None:
            filters["reminder_id"] = reminder_id
            
        if client_id is not None:
            filters["client_id"] = client_id
            
        if status is not None:
            filters["status"] = status
            
        if notification_type is not None:
            filters["notification_type"] = notification_type
            
        if start_date is not None:
            filters["start_date"] = start_date
            
        if end_date is not None:
            filters["end_date"] = end_date
        
        # Get filtered notifications
        notifications = self.repository.get_filtered(db, **filters)
        
        # Create detailed notifications
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
            
            # Create NotificationDetail object
            notification_data = NotificationSchema.model_validate(notification).model_dump()
            detailed_notifications.append(
                NotificationDetail(
                    **notification_data,
                    reminder_title=reminder.title,
                    client_name=client.name
                )
            )
        
        return detailed_notifications
    
    @handle_exceptions(error_message="Failed to get notification stats")
    def get_notification_stats(
        self, 
        db: Session
    ) -> Dict[str, Any]:
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
            Notification.created_at >= datetime.utcnow() - timedelta(days=1)
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
            "generated_at": datetime.utcnow().isoformat()
        }
        
    @with_transaction
    @handle_exceptions(error_message="Failed to clear old notifications")
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
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        # Get old failed notifications
        filters = {
            "status": NotificationStatusEnum.FAILED,
            "end_date": cutoff_date,  # Only get notifications created before this date
            "limit": limit
        }
        old_failed_notifications = self.repository.get_filtered(db, **filters)
        
        # Delete each notification
        count = 0
        for notification in old_failed_notifications:
            self.repository.delete(db, id=notification.id)
            count += 1
        
        return count
        
    @with_transaction
    @handle_exceptions(error_message="Failed to resend all failed notifications")
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
        # Get failed notifications
        filters = {
            "status": NotificationStatusEnum.FAILED,
            "limit": limit
        }
        failed_notifications = self.repository.get_filtered(db, **filters)
        
        # Reset status to PENDING for each notification
        count = 0
        for notification in failed_notifications:
            self.repository.update(
                db, 
                db_obj=notification, 
                obj_in={"status": NotificationStatusEnum.PENDING, "error_message": None}
            )
            count += 1
        
        return count

# Create singleton instance
notification_service = NotificationService() 