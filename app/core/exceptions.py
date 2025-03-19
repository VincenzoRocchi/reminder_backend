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