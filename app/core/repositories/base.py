from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from pydantic import BaseModel
from datetime import datetime

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
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Optional[ModelType]: Record if found, None otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
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
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType | Dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic model or dict with data to create
            
        Returns:
            ModelType: Created record
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()
            
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
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
        """
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
    
    def delete(self, db: Session, *, id: int) -> ModelType:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            ModelType: Deleted record
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
    
    def exists(self, db: Session, *, id: int) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            bool: True if record exists, False otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
    
    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            db: Database session
            filters: Optional dictionary of filters
            
        Returns:
            int: Number of records
        """
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
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
        """
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