class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UserNotFoundError(AppException):
    """Raised when a user is not found."""
    pass

class UserAlreadyExistsError(AppException):
    """Raised when trying to create a user that already exists."""
    pass

class InvalidCredentialsError(AppException):
    """Raised when user credentials are invalid."""
    pass

class ClientNotFoundError(AppException):
    """Raised when a client is not found."""
    pass

class ClientAlreadyExistsError(AppException):
    """Raised when trying to create a client that already exists."""
    pass

class RedisError(AppException):
    """Raised when Redis operations fail."""
    pass

class SensitiveDataStorageError(AppException):
    """Raised when sensitive data storage operations fail."""
    pass

class InvalidConfigurationError(AppException):
    """Raised when configuration is invalid."""
    pass

class EncryptionError(AppException):
    """Exception for encryption/decryption failures"""
    def __init__(self, message: str = "Encryption operation failed"):
        super().__init__(
            message=message,
            code="ENCRYPTION_FAILURE",
            status_code=500
        )

class SecurityException(AppException):
    """Base exception for security-related errors"""
    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        super().__init__(
            message=message,
            code=code,
            status_code=403
        )

class TokenExpiredError(SecurityException):
    """Exception for expired tokens"""
    def __init__(self):
        super().__init__(
            message="Authentication token has expired",
            code="TOKEN_EXPIRED"
        )

class TokenInvalidError(SecurityException):
    """Exception for invalid tokens"""
    def __init__(self, reason: str = "Token validation failed"):
        super().__init__(
            message=f"Invalid token: {reason}",
            code="TOKEN_INVALID"
        )

class TokenRevokedError(SecurityException):
    """Exception for revoked/blacklisted tokens"""
    def __init__(self):
        super().__init__(
            message="Token has been revoked",
            code="TOKEN_REVOKED"
        )
        
class InsufficientPermissionsError(SecurityException):
    """Exception for permission issues"""
    def __init__(self, required_permission: str = None):
        message = "Insufficient permissions"
        if required_permission:
            message += f": {required_permission} required"
            
        super().__init__(
            message=message,
            code="INSUFFICIENT_PERMISSIONS"
        )
        
class DatabaseError(AppException):
    """Exception for database operation failures"""
    def __init__(self, message: str = "Database operation failed", details: str = None):
        error_message = message
        if details:
            error_message += f": {details}"
            
        super().__init__(
            message=error_message,
            code="DATABASE_ERROR",
            status_code=500
        )
        
class ServiceError(AppException):
    """Exception for external service operations failure"""
    def __init__(self, service: str, message: str, details: str = None):
        error_message = f"{service} service error: {message}"
        if details:
            error_message += f" - {details}"
            
        super().__init__(
            message=error_message,
            code=f"{service.upper()}_SERVICE_ERROR",
            status_code=500
        )
        
class ValidationError(AppException):
    """Exception for data validation failures"""
    def __init__(self, field: str = None, message: str = "Validation failed"):
        error_message = message
        if field:
            error_message = f"Validation failed for {field}: {message}"
            
        super().__init__(
            message=error_message,
            code="VALIDATION_ERROR",
            status_code=422
        )

class ReminderNotFoundError(Exception):
    """Raised when a reminder is not found."""
    pass

class ReminderAlreadyExistsError(Exception):
    """Raised when trying to create a reminder that already exists."""
    pass

class InvalidReminderConfigurationError(Exception):
    """Raised when reminder configuration is invalid."""
    pass

class EmailConfigurationNotFoundError(Exception):
    """Raised when an email configuration is not found."""
    pass

class EmailConfigurationAlreadyExistsError(Exception):
    """Raised when trying to create an email configuration that already exists."""
    pass

class SenderIdentityNotFoundError(Exception):
    """Raised when a sender identity is not found."""
    pass

class SenderIdentityAlreadyExistsError(Exception):
    """Raised when trying to create a sender identity that already exists."""
    pass

class NotificationNotFoundError(Exception):
    """Raised when a notification is not found."""
    pass

class ReminderRecipientNotFoundError(Exception):
    """Raised when a reminder recipient is not found."""
    pass

class AuthError(Exception):
    """Base class for authentication errors."""
    pass

class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""
    pass

class TokenError(AuthError):
    """Base class for token-related errors."""
    pass

class TokenExpiredError(TokenError):
    """Raised when a token has expired."""
    pass

class TokenInvalidError(TokenError):
    """Raised when a token is invalid."""
    pass

class UserNotFoundError(AuthError):
    """Raised when a user is not found."""
    pass