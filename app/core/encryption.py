# ----------------------------------------------------------------------
# PRODUCTION NOTES:
#
# 1. Key and Salt Management:
#    - Ensure SECRET_KEY in settings is sufficiently long and complex.
#    - Verify that the ENCRYPTION_SALT value (if set via environment variable)
#      is managed securely and consistently across deployments.
#
# 2. Algorithms and Derivation Parameters:
#    - The parameters used (e.g., iterations in PBKDF2HMAC) are adequate for the production environment;
#      consider increasing the number of iterations if the CPU load allows it.
#
# 3. Logging:
#    - In production, set an appropriate logging level (e.g., WARNING or ERROR) to avoid
#      exposing sensitive information or generating overly verbose logs.
#
# 4. General Security:
#    - Verify that the use of encryption mechanisms (Fernet for strings, AES for bytes) is
#      compliant with the application's security requirements.
#    - Ensure that generated keys are never hard-coded and are provided through a
#      secure secret management system or secure environment variables.
#
# 5. Pydantic Integration:
#    - If you're using the create_encrypted_model method for Pydantic models, verify that the validation
#      and decryption logic works correctly in all production use cases.
#
# In summary, in production you will need to:
#    - Use a robust secret key and a consistent, secure salt.
#    - Evaluate key derivation parameters to ensure security without compromising
#      performance.
#    - Configure logging so that sensitive information is not exposed.

import base64
import os
import logging
from typing import TypeVar, Generic, Optional, Union, Type, Any, cast, Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from pydantic import BaseModel, SecretStr, create_model, field_validator

from app.core.settings import settings
from app.core.exceptions import EncryptionError

logger = logging.getLogger(__name__)

# Type variable for generic model handling with Pydantic
T = TypeVar('T', bound=BaseModel)


class EncryptionService:
    """
    Centralized service for handling encryption and decryption operations across the application.
    
    Features:
    - Multiple encryption strategies (Fernet, AES)
    - Seamless integration with Pydantic models
    - Support for async operations where beneficial
    - Type annotations for better IDE integration
    
    This service ensures consistent encryption handling throughout the application
    while maintaining compatibility with FastAPI's data validation approach.
    """
    
    def __init__(self):
        """
        Initialize the encryption service with keys derived from application settings.
        Uses SECRET_KEY from settings with proper key derivation functions.
        """
        # Initialize Fernet encryption (suitable for most string encryption needs)
        self._fernet_key = self._derive_fernet_key(settings.SECRET_KEY)
        self._fernet = Fernet(self._fernet_key)
        
        # Initialize AES encryption (for binary data or specialized needs)
        salt = self._get_or_create_salt()
        self._aes_key = self._derive_aes_key(settings.SECRET_KEY, salt)
        
        logger.debug("Encryption service initialized")
    
    def _get_or_create_salt(self) -> bytes:
        """
        Get salt from environment or create a stable one based on settings.
        In production, this should be stored securely and consistently.
        
        Returns:
            Bytes to use as salt for key derivation
        """
        # Check if we have a salt in environment variables
        env_salt = os.environ.get("ENCRYPTION_SALT")
        if env_salt:
            return base64.b64decode(env_salt)
        
        # Create a salt derived from SECRET_KEY to ensure consistency
        # This is acceptable if SECRET_KEY is strong and secure
        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(f"{settings.SECRET_KEY}_salt_value".encode())
        return hasher.finalize()[:16]  # Use first 16 bytes as salt
    
    def _derive_fernet_key(self, secret_key: str) -> bytes:
        """
        Derive a secure Fernet key from the application's secret key.
        
        Args:
            secret_key: The application's secret key
            
        Returns:
            A URL-safe base64-encoded 32-byte key suitable for Fernet
        """
        if not secret_key or len(secret_key) < 32:
            logger.warning("Secret key too short for secure encryption. Consider using a longer key.")
        
        # Use PBKDF2 for secure key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._get_or_create_salt(),
            iterations=100000,  # High iteration count for better security
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return key
    
    def _derive_aes_key(self, secret_key: str, salt: bytes) -> bytes:
        """
        Derive a secure key for AES encryption from the application's secret key.
        
        Args:
            secret_key: The application's secret key
            salt: Salt value for key derivation
            
        Returns:
            A 32-byte key suitable for AES-256
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits (AES-256)
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(secret_key.encode())
    
    # Synchronous encryption methods
    
    def encrypt_string(self, data: str) -> str:
        """
        Encrypt a string using Fernet symmetric encryption.
        
        Args:
            data: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not data:
            return ""
        
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return f"v1:{encrypted_data.decode()}"
        except Exception as e:
            logger.error(f"Error encrypting string: {str(e)}")
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    def decrypt_string(self, encrypted_data: str) -> str:
        """
        Decrypt a Fernet-encrypted string.
        
        Args:
            encrypted_data: Encrypted string (base64-encoded)
            
        Returns:
            Decrypted string
        """
        if not encrypted_data:
            return ""
        
        try:
            # Handle versioned encryption
            if encrypted_data.startswith("v1:"):
                # Version 1 encryption scheme
                actual_data = encrypted_data[3:]  # Remove "v1:" prefix
                decrypted_data = self._fernet.decrypt(actual_data.encode())
                return decrypted_data.decode()
            else:
                decrypted_data = self._fernet.decrypt(encrypted_data.encode())
                return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting string: {str(e)}")
            raise EncryptionError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt all string values in a dictionary.
        
        Args:
            data: Dictionary with string values to encrypt
            
        Returns:
            Dictionary with encrypted string values
        """
        if not data:
            return {}
            
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.encrypt_string(value)
            elif isinstance(value, dict):
                result[key] = self.encrypt_dict(value)
            elif isinstance(value, (int, float, bool, type(None))):
                # Non-string primitive types are stored as-is
                result[key] = value
            else:
                # Convert other types to string and encrypt
                result[key] = self.encrypt_string(str(value))
                
        return result
    
    def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all encrypted string values in a dictionary.
        
        Args:
            data: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        if not data:
            return {}
            
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.decrypt_string(value)
            elif isinstance(value, dict):
                result[key] = self.decrypt_dict(value)
            else:
                # Non-encrypted values (like numbers, booleans) remain unchanged
                result[key] = value
                
        return result
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt binary data using AES-256-CBC with PKCS7 padding.
        
        Args:
            data: Binary data to encrypt
            
        Returns:
            Encrypted bytes (IV + ciphertext)
        """
        if not data:
            return b''
        
        try:
            # Generate a random IV (Initialization Vector)
            iv = os.urandom(16)  # 16 bytes for AES
            
            # Apply PKCS7 padding
            padder = PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data) + padder.finalize()
            
            # Create and use the cipher
            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Return IV + ciphertext
            return iv + ciphertext
        except Exception as e:
            logger.error(f"Error encrypting bytes: {str(e)}")
            raise EncryptionError(f"Byte encryption failed: {str(e)}")
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt binary data that was encrypted with AES-256-CBC.
        
        Args:
            encrypted_data: Encrypted bytes (IV + ciphertext)
            
        Returns:
            Decrypted bytes
        """
        if not encrypted_data or len(encrypted_data) <= 16:
            return b''
            
        try:
            # Split IV and ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Create and use the cipher
            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            unpadder = PKCS7(algorithms.AES.block_size).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data
        except Exception as e:
            logger.error(f"Error decrypting bytes: {str(e)}")
            raise EncryptionError(f"Byte decryption failed: {str(e)}")
    
    # Async methods for better integration with FastAPI
    # These methods are thin wrappers around sync methods since cryptographic
    # operations are CPU-bound, not I/O-bound, but they provide an async
    # interface for consistency in async code contexts
    
    async def aencrypt_string(self, data: str) -> str:
        """
        Async wrapper for string encryption.
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string
        """
        return self.encrypt_string(data)
    
    async def adecrypt_string(self, encrypted_data: str) -> str:
        """
        Async wrapper for string decryption.
        
        Args:
            encrypted_data: Encrypted string to decrypt
            
        Returns:
            Decrypted string
        """
        return self.decrypt_string(encrypted_data)
    
    async def aencrypt_bytes(self, data: bytes) -> bytes:
        """
        Async wrapper for bytes encryption.
        
        Args:
            data: Bytes to encrypt
            
        Returns:
            Encrypted bytes
        """
        return self.encrypt_bytes(data)
    
    async def adecrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        Async wrapper for bytes decryption.
        
        Args:
            encrypted_data: Encrypted bytes to decrypt
            
        Returns:
            Decrypted bytes
        """
        return self.decrypt_bytes(encrypted_data)
    
    # Methods specifically for Pydantic integration
    
    def create_encrypted_model(self, model_class: Type[T], 
                              encrypt_fields: list[str]) -> Type[T]:
        """
        Create a subclass of a Pydantic model with automatic field encryption/decryption.
        
        Args:
            model_class: Base Pydantic model class to enhance
            encrypt_fields: List of field names to encrypt
            
        Returns:
            Enhanced model class with encryption capabilities
        """
        # Get the field definitions from the original model
        field_definitions = {
            field_name: (field_info.annotation, field_info.get_default())
            for field_name, field_info in model_class.model_fields.items()
        }
        
        # Create a new model class with the same fields
        encrypted_model = create_model(
            f"Encrypted{model_class.__name__}",
            __base__=model_class,
            **field_definitions
        )
        
        # Add validators for the encrypted fields
        for field_name in encrypt_fields:
            # Only add validators if the field exists
            if field_name in field_definitions:
                # Add encryption on field assignment
                setattr(encrypted_model, f"encrypt_{field_name}", 
                       field_validator(field_name, mode='before')(
                           lambda v, self=self, field=field_name: 
                               self.encrypt_string(v) if v and isinstance(v, str) else v
                       ))
                
                # Add decryption when accessing the field
                # This requires modifying the model's __getattribute__ method
                original_getattribute = encrypted_model.__getattribute__
                
                def enhanced_getattribute(instance, name):
                    value = original_getattribute(instance, name)
                    if name in encrypt_fields and isinstance(value, str):
                        try:
                            return self.decrypt_string(value)
                        except:
                            # If decryption fails, return the raw value
                            return value
                    return value
                
                encrypted_model.__getattribute__ = enhanced_getattribute
        
        return encrypted_model
    
    def encrypt_model_field(self, value: Any) -> Any:
        """
        Utility method to encrypt a value based on its type.
        Handles strings, bytes, and converts other types to strings.
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value
        """
        if value is None:
            return None
        
        if isinstance(value, SecretStr):
            # Handle Pydantic SecretStr fields
            return self.encrypt_string(value.get_secret_value())
        elif isinstance(value, str):
            return self.encrypt_string(value)
        elif isinstance(value, bytes):
            return self.encrypt_bytes(value)
        else:
            # Convert to string and encrypt
            return self.encrypt_string(str(value))
    
    def decrypt_model_field(self, value: Any, field_type: Type = str) -> Any:
        """
        Decrypt a field value and convert to the specified type.
        
        Args:
            value: Encrypted value
            field_type: Type to convert the decrypted value to
            
        Returns:
            Decrypted value of the specified type
        """
        if value is None:
            return None
            
        if isinstance(value, str):
            decrypted = self.decrypt_string(value)
            
            # Convert to the target type
            if field_type == str:
                return decrypted
            elif field_type == int:
                return int(decrypted)
            elif field_type == float:
                return float(decrypted)
            elif field_type == bool:
                return decrypted.lower() in ('true', '1', 'yes', 'y')
            elif field_type == SecretStr:
                return SecretStr(decrypted)
            else:
                return decrypted
        elif isinstance(value, bytes):
            return self.decrypt_bytes(value)
        else:
            # Return as is if it doesn't appear to be encrypted
            return value


# Create singleton instance for application-wide use
encryption_service = EncryptionService()