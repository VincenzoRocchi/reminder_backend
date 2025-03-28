from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from pydantic import BaseModel
from datetime import datetime

from app.core.exceptions import DatabaseError, AppException

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class with common CRUD operations.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with model class.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> ModelType:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            ModelType: Record if found
            
        Raises:
            DatabaseError: If record not found
        """
        result = db.query(self.model).filter(self.model.id == id).first()
        if not result:
            raise DatabaseError(f"{self.model.__name__} with ID {id} not found")
        return result
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of filters
            
        Returns:
            List[ModelType]: List of records
        """
        try:
            query = db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get {self.model.__name__} records", str(e))
    
    def create(self, db: Session, *, obj_in: CreateSchemaType | Dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic model or dict with data to create
            
        Returns:
            ModelType: Created record
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            if isinstance(obj_in, dict):
                obj_in_data = obj_in
            else:
                obj_in_data = obj_in.model_dump()
                
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to create {self.model.__name__}", str(e))
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing database record
            obj_in: Pydantic model or dict with update data
            
        Returns:
            ModelType: Updated record
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            obj_data = db_obj.__dict__
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
                
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
                    
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to update {self.model.__name__} with ID {db_obj.id}", str(e))
    
    def delete(self, db: Session, *, id: int) -> ModelType:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            ModelType: Deleted record
            
        Raises:
            DatabaseError: If record not found or deletion fails
        """
        try:
            obj = self.get(db, id=id)  # This will raise an exception if not found
            db.delete(obj)
            db.commit()
            return obj
        except AppException:
            raise  # Re-raise app exceptions as they are
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to delete {self.model.__name__} with ID {id}", str(e))
    
    def exists(self, db: Session, *, id: int) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check if {self.model.__name__} exists", str(e))
    
    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            db: Database session
            filters: Optional dictionary of filters
            
        Returns:
            int: Number of records
            
        Raises:
            DatabaseError: If count operation fails
        """
        try:
            query = db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            raise DatabaseError(f"Failed to count {self.model.__name__} records", str(e))
    
    def get_filtered(
        self, 
        db: Session, 
        *,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        reminder_id: Optional[int] = None,
        client_id: Optional[int] = None,
        status: Optional[Any] = None,
        notification_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> List[ModelType]:
        """
        Get records with flexible filtering options.
        
        Args:
            db: Database session
            user_id: Optional User ID for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            reminder_id: Filter by reminder ID
            client_id: Filter by client ID
            status: Filter by status
            notification_type: Filter by notification type
            start_date: Filter by records created after this date
            end_date: Filter by records created before this date
            **kwargs: Additional filters
            
        Returns:
            List[ModelType]: List of records
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            # Start with base query
            query = db.query(self.model)
            
            # Add filters
            if user_id is not None and hasattr(self.model, 'user_id'):
                query = query.filter(self.model.user_id == user_id)
                
            if reminder_id is not None and hasattr(self.model, 'reminder_id'):
                query = query.filter(self.model.reminder_id == reminder_id)
                
            if client_id is not None and hasattr(self.model, 'client_id'):
                query = query.filter(self.model.client_id == client_id)
                
            if status is not None and hasattr(self.model, 'status'):
                query = query.filter(self.model.status == status)
                
            if notification_type is not None and hasattr(self.model, 'notification_type'):
                query = query.filter(self.model.notification_type == notification_type)
                
            if start_date is not None and hasattr(self.model, 'created_at'):
                query = query.filter(self.model.created_at >= start_date)
                
            if end_date is not None and hasattr(self.model, 'created_at'):
                query = query.filter(self.model.created_at <= end_date)
                
            # Add any additional filters
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            
            # Order by creation date (newest first) if the model has created_at
            if hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())
                
            # Apply pagination
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get filtered {self.model.__name__} records", str(e)) 