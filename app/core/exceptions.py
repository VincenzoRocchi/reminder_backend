from fastapi import status
from typing import Optional, Any, Dict, List

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

# User related exceptions
class UserNotFoundError(AppException):
    """Raised when a user is not found."""
    def __init__(self, message: str = "User not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND"
        )

class UserAlreadyExistsError(AppException):
    """Raised when trying to create a user that already exists."""
    def __init__(self, message: str = "User already exists"):
        super().__init__(
            message=message, 
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_ALREADY_EXISTS"
        )

# Client related exceptions
class ClientNotFoundError(AppException):
    """Raised when a client is not found."""
    def __init__(self, message: str = "Client not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CLIENT_NOT_FOUND"
        )

class ClientAlreadyExistsError(AppException):
    """Raised when trying to create a client that already exists."""
    def __init__(self, message: str = "Client already exists"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CLIENT_ALREADY_EXISTS"
        )

# Infrastructure exceptions
class RedisError(AppException):
    """Raised when Redis operations fail."""
    def __init__(self, message: str = "Redis operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="REDIS_ERROR"
        )

class SensitiveDataStorageError(AppException):
    """Raised when sensitive data storage operations fail."""
    def __init__(self, message: str = "Sensitive data storage operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SENSITIVE_DATA_STORAGE_ERROR"
        )

class InvalidConfigurationError(AppException):
    """Raised when configuration is invalid."""
    def __init__(self, message: str = "Invalid configuration"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INVALID_CONFIGURATION"
        )

class EncryptionError(AppException):
    """Exception for encryption/decryption failures"""
    def __init__(self, message: str = "Encryption operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="ENCRYPTION_FAILURE"
        )

# Security exceptions
class SecurityException(AppException):
    """Base exception for security-related errors"""
    def __init__(self, message: str, error_code: str = "SECURITY_ERROR"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code
        )

class TokenExpiredError(SecurityException):
    """Exception for expired tokens"""
    def __init__(self, message: str = "Authentication token has expired"):
        super().__init__(
            message=message,
            error_code="TOKEN_EXPIRED"
        )

class TokenInvalidError(SecurityException):
    """Exception for invalid tokens"""
    def __init__(self, message: str = "Token validation failed"):
        super().__init__(
            message=message,
            error_code="TOKEN_INVALID"
        )

class TokenRevokedError(SecurityException):
    """Exception for revoked/blacklisted tokens"""
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(
            message=message,
            error_code="TOKEN_REVOKED"
        )
        
class InsufficientPermissionsError(SecurityException):
    """Exception for permission issues"""
    def __init__(self, required_permission: str = None):
        message = "Insufficient permissions"
        if required_permission:
            message += f": {required_permission} required"
            
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS"
        )
        
class DatabaseError(AppException):
    """Exception for database operation failures"""
    def __init__(self, message: str = "Database operation failed", details: str = None):
        error_message = message
        if details:
            error_message += f": {details}"
            
        super().__init__(
            message=error_message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )
        
class ServiceError(AppException):
    """Exception for external service operations failure"""
    def __init__(self, service: str, message: str, details: str = None):
        error_message = f"{service} service error: {message}"
        
        super().__init__(
            message=error_message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=f"{service.upper()}_SERVICE_ERROR",
            details=details
        )
        
class ValidationError(AppException):
    """Exception for data validation failures"""
    def __init__(self, field: str = None, message: str = "Validation failed"):
        error_message = message
        if field:
            error_message = f"Validation failed for {field}: {message}"
            
        super().__init__(
            message=error_message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )

# Reminder related exceptions
class ReminderNotFoundError(AppException):
    """Raised when a reminder is not found."""
    def __init__(self, message: str = "Reminder not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="REMINDER_NOT_FOUND"
        )

class ReminderAlreadyExistsError(AppException):
    """Raised when trying to create a reminder that already exists."""
    def __init__(self, message: str = "Reminder already exists"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="REMINDER_ALREADY_EXISTS"
        )

class InvalidReminderConfigurationError(AppException):
    """Raised when reminder configuration is invalid."""
    def __init__(self, message: str = "Invalid reminder configuration"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_REMINDER_CONFIGURATION"
        )

# Email configuration exceptions
class EmailConfigurationNotFoundError(AppException):
    """Raised when an email configuration is not found."""
    def __init__(self, message: str = "Email configuration not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="EMAIL_CONFIGURATION_NOT_FOUND"
        )

class EmailConfigurationAlreadyExistsError(AppException):
    """Raised when trying to create an email configuration that already exists."""
    def __init__(self, message: str = "Email configuration already exists"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="EMAIL_CONFIGURATION_ALREADY_EXISTS"
        )

# Sender identity exceptions
class SenderIdentityNotFoundError(AppException):
    """Raised when a sender identity is not found."""
    def __init__(self, message: str = "Sender identity not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SENDER_IDENTITY_NOT_FOUND"
        )

class SenderIdentityAlreadyExistsError(AppException):
    """Raised when trying to create a sender identity that already exists."""
    def __init__(self, message: str = "Sender identity already exists"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="SENDER_IDENTITY_ALREADY_EXISTS"
        )

# Notification exceptions
class NotificationNotFoundError(AppException):
    """Raised when a notification is not found."""
    def __init__(self, message: str = "Notification not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOTIFICATION_NOT_FOUND"
        )

class ReminderRecipientNotFoundError(AppException):
    """Raised when a reminder recipient is not found."""
    def __init__(self, message: str = "Reminder recipient not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="REMINDER_RECIPIENT_NOT_FOUND"
        )

# Authentication exceptions
class AuthError(AppException):
    """Base class for authentication errors."""
    def __init__(self, message: str, error_code: str = "AUTH_ERROR"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code
        )

class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS"
        )