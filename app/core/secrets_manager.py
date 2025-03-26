# app/core/secrets_manager.py
import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.encryption import encryption_service
from app.core.settings import settings
from app.core.exceptions import AppException, EncryptionError, SecurityException, InvalidConfigurationError

logger = logging.getLogger(__name__)

class SecretsError(SecurityException):
    """Exception for secrets management errors"""
    def __init__(self, message: str, code: str = "SECRETS_ERROR"):
        super().__init__(
            message=message,
            code=code
        )

class SecretNotFoundError(SecretsError):
    """Exception for missing required secrets"""
    def __init__(self, secret_key: str):
        super().__init__(
            message=f"Required secret not found: {secret_key}",
            code="SECRET_NOT_FOUND"
        )

class EncryptedSecretsManager:
    """
    Manages application secrets using encrypted file storage.
    Integrates with the existing encryption_service.
    """
    
    def __init__(self):
        self.env = settings.ENV
        self.secrets_dir = Path("./secrets")
        self.secrets_path = self.secrets_dir / f"secrets.{self.env}.enc"
        self._secrets_cache = {}
        self._loaded = False
        
        # Ensure secrets directory exists
        self.secrets_dir.mkdir(exist_ok=True)
    
    def _load_secrets(self) -> None:
        """Load encrypted secrets from file"""
        if self._loaded:
            return
            
        try:
            if not self.secrets_path.exists():
                logger.warning(f"Secrets file not found: {self.secrets_path}")
                self._secrets_cache = {}
                return
                
            with open(self.secrets_path, "r") as f:
                encrypted_data = f.read().strip()
                
            if not encrypted_data:
                logger.warning("Secrets file is empty")
                self._secrets_cache = {}
                return
                
            # Decrypt using existing encryption service
            try:
                decrypted_data = encryption_service.decrypt_string(encrypted_data)
                self._secrets_cache = json.loads(decrypted_data)
                self._loaded = True
                logger.info(f"Successfully loaded secrets for {self.env} environment")
            except Exception as e:
                raise EncryptionError(f"Failed to decrypt secrets: {str(e)}")
            
        except EncryptionError:
            # Re-raise encryption errors directly
            raise
        except Exception as e:
            # Wrap other errors in SecretsError
            raise SecretsError(f"Failed to load secrets: {str(e)}")
    
    def get_secret(self, category: str, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get a specific secret by category and key.
        
        Args:
            category: Category of secret (e.g., 'database', 'security')
            key: Secret key name
            default: Default value if secret not found
            required: If True, raise exception when secret not found
            
        Returns:
            Secret value or default
            
        Raises:
            SecretNotFoundError: If required=True and secret not found
        """
        try:
            self._load_secrets()
            
            category_secrets = self._secrets_cache.get(category, {})
            value = category_secrets.get(key, default)
            
            if value is None and required:
                raise SecretNotFoundError(f"{category}.{key}")
                
            return value
            
        except (EncryptionError, SecretNotFoundError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            # Wrap other errors
            raise SecretsError(f"Error accessing secret {category}.{key}: {str(e)}")
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all secrets for a category"""
        try:
            self._load_secrets()
            return self._secrets_cache.get(category, {}).copy()
        except (EncryptionError, SecretNotFoundError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            # Wrap other errors
            raise SecretsError(f"Error accessing category {category}: {str(e)}")
    
    def set_secret(self, category: str, key: str, value: Any) -> bool:
        """
        Set a secret value and save to encrypted file
        
        Args:
            category: Category of secret
            key: Secret key name
            value: Secret value
            
        Returns:
            True if successful
        """
        try:
            # Load existing secrets first
            self._load_secrets()
            
            # Create category if it doesn't exist
            if category not in self._secrets_cache:
                self._secrets_cache[category] = {}
                
            # Set the value
            self._secrets_cache[category][key] = value
            
            # Save to file
            self._save_secrets()
            
            return True
            
        except EncryptionError:
            # Re-raise encryption errors directly
            raise
        except Exception as e:
            # Wrap other errors
            raise SecretsError(f"Error setting secret {category}.{key}: {str(e)}")
    
    def _save_secrets(self) -> None:
        """Save secrets to encrypted file"""
        try:
            # Ensure directory exists
            self.secrets_dir.mkdir(exist_ok=True)
            
            # Convert to JSON and encrypt
            secrets_json = json.dumps(self._secrets_cache)
            try:
                encrypted_data = encryption_service.encrypt_string(secrets_json)
            except Exception as e:
                raise EncryptionError(f"Failed to encrypt secrets: {str(e)}")
            
            # Write to file
            with open(self.secrets_path, "w") as f:
                f.write(encrypted_data)
                
            logger.info(f"Successfully saved secrets for {self.env} environment")
            
        except EncryptionError:
            # Re-raise encryption errors
            raise
        except Exception as e:
            # Wrap other errors
            raise SecretsError(f"Failed to save secrets: {str(e)}")

# Create singleton instance
secrets_manager = EncryptedSecretsManager()