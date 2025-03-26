class AppException(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, code: str = "GENERIC_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class EncryptionError(AppException):
    """Exception for encryption/decryption failures"""
    def __init__(self, message: str = "Encryption operation failed"):
        super().__init__(
            message=message,
            code="ENCRYPTION_FAILURE",
            status_code=500
        )

class InvalidConfigurationError(AppException):
    """Exception for invalid service configurations"""
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"Invalid {service} configuration: {reason}",
            code="INVALID_CONFIGURATION",
            status_code=400
        )

class SecurityException(AppException):
    """Base exception for security-related errors"""
    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        super().__init__(
            message=message,
            code=code,
            status_code=403
        )

class SensitiveDataStorageError(SecurityException):
    """Exception for failed sensitive data storage"""
    def __init__(self, field: str):
        super().__init__(
            message=f"Failed to securely store {field}",
            code="SENSITIVE_DATA_STORAGE_FAILURE"
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