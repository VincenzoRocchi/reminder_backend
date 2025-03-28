# Error Handling Guide

This document outlines the standardized approach to error handling in the Reminder App backend.

## Core Principles

1. **Consistency**: All error handling should follow the same patterns throughout the codebase
2. **Explicit Error Types**: Use specific exception types rather than returning None/booleans
3. **Centralized Handling**: Use decorators and utilities for common error handling patterns
4. **Proper Transaction Management**: Ensure database transactions are properly committed or rolled back

## Exception Hierarchy

All application exceptions inherit from `AppException` defined in `app/core/exceptions.py`:

- `AppException` - Base exception for all application errors
  - `UserNotFoundError`, `UserAlreadyExistsError`, etc. - Domain-specific exceptions
  - `SecurityException` - Base for security-related errors
  - `DatabaseError` - Database operation failures
  - `ServiceError` - External service failures
  - `ValidationError` - Data validation failures

## Error Handling Utilities

We provide utility decorators in `app/core/error_handling.py` to standardize error handling:

### 1. `handle_exceptions` Decorator

This decorator provides standardized exception handling for service methods:

```python
@handle_exceptions(error_message="Failed to get user")
def get_user(db: Session, user_id: int) -> User:
    # Implementation...
```

Parameters:

- `error_message`: Base message to use when creating an exception
- `log_error`: Whether to log the exception (default: True)
- `reraise`: Whether to reraise the exception (True) or return None (False)

### 2. `with_transaction` Decorator

This decorator handles database transactions and ensures proper rollback in case of exceptions:

```python
@with_transaction
@handle_exceptions(error_message="Failed to create user")
def create_user(db: Session, *, user_in: UserCreate) -> User:
    # Implementation with db operations...
```

## Best Practices

### Repository Layer

- Methods should raise appropriate exceptions rather than returning None
- Use `DatabaseError` for database-related issues
- Document the exceptions a method can raise in its docstring

Example:

```python
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
```

### Service Layer

- Use the `handle_exceptions` decorator for consistent error handling
- Use the `with_transaction` decorator for methods that modify data
- Use specific domain exceptions (UserNotFoundError, etc.) for business logic
- Chain decorators with `with_transaction` first, then `handle_exceptions`

Example:

```python
@with_transaction
@handle_exceptions(error_message="Failed to update user")
def update_user(self, db: Session, *, user_id: int, user_in: UserUpdate) -> User:
    user = self.repository.get(db, id=user_id)
    if not user:
        raise UserNotFoundError(f"User with ID {user_id} not found")
    return self.repository.update(db, db_obj=user, obj_in=user_in)
```

### API/Controller Layer

- Let exceptions propagate to the global exception handlers
- Use the proper status codes in your exceptions
- The global handlers will format the response appropriately

## Migration Guide

When updating existing code:

1. Replace boolean returns with appropriate exceptions
2. Add `@handle_exceptions` decorators to service methods
3. Add `@with_transaction` decorators to methods that modify data
4. Update documentation to reflect the exceptions that can be raised

## Integration with FastAPI

The application registers global exception handlers for all application exceptions in `app/core/exception_handlers.py`. These handlers provide consistent JSON error responses with appropriate status codes.
