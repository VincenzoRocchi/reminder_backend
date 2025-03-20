# ----------------------------------------------------------------------
# NOTE PER LA PRODUZIONE:
#
# 1. Sicurezza e Crittografia:
#    - Verifica che il modulo `encryption_service` utilizzi chiavi e algoritmi
#      adeguati per la produzione. Assicurati che le chiavi di cifratura siano
#      gestite in modo sicuro (ad es. tramite variabili d'ambiente o un secret manager).
#
# 2. Validazione dei Dati Sensibili:
#    - Conferma che la logica di validazione (ad es. per SMTP, Twilio, WhatsApp)
#      sia sufficientemente rigorosa in produzione. Potrebbe essere necessario abilitare
#      la modalità "strict" per garantire la conformità ai requisiti di sicurezza.
#
# 3. Logging:
#    - In produzione, regola il livello di logging per evitare di scrivere
#      informazioni troppo dettagliate (specialmente errori che contengono dati sensibili).
#
# 4. Prestazioni e Constrain:
#    - Assicurati che i tipi di dati e le dimensioni dei campi siano ottimali per il
#      carico del database in produzione. Considera l'aggiunta di indici sui campi
#      più frequentemente interrogati.
#
# 5. Gestione degli Errori:
#    - Rivedi il comportamento in caso di errori di cifratura/decrittazione per
#      garantire che non vengano rivelate informazioni sensibili all'utente finale.
#
# In sintesi, il codice del modello rimane sostanzialmente invariato in produzione,
# ma dovrai concentrarti su:
#    - La configurazione sicura e aggiornata del servizio di crittografia.
#    - Il corretto bilanciamento tra validazioni stringenti e usabilità.
#    - Un logging e una gestione degli errori che non compromettano la sicurezza.

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import Optional
from datetime import datetime
import logging
import uuid

from app.core.settings import settings
from app.database import Base
from app.core.encryption import encryption_service
from app.core.exceptions import (
    EncryptionError,
    InvalidConfigurationError,
    SensitiveDataStorageError
)

logger = logging.getLogger(__name__)

class Business(Base):
    """
    Business database model with encrypted sensitive fields
    
    This model handles encryption and decryption of sensitive data transparently
    using Python properties. The actual encrypted values are stored in columns
    prefixed with an underscore, while clean accessor properties provide
    automatic encryption/decryption.
    """
    __tablename__ = "businesses"
    
    # Regular fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    _phone_number: Mapped[Optional[str]] = mapped_column("phone_number", String(20))  # Encrypted field
    address: Mapped[Optional[str]] = mapped_column(String(500))
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Email notification settings
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255))
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255))
    _smtp_password: Mapped[Optional[str]] = mapped_column("smtp_password", String(500))
    email_from: Mapped[Optional[str]] = mapped_column(String(255))
    
    # SMS notification settings
    twilio_account_sid: Mapped[Optional[str]] = mapped_column(String(255))
    _twilio_auth_token: Mapped[Optional[str]] = mapped_column("twilio_auth_token", String(500))
    twilio_phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    
    # WhatsApp notification settings
    _whatsapp_api_key: Mapped[Optional[str]] = mapped_column("whatsapp_api_key", String(500))
    whatsapp_api_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships
    owner = relationship("User", back_populates="businesses")
    reminders = relationship("Reminder", back_populates="business", cascade="all, delete-orphan")

    # Phone number encryption
    @property
    def phone_number(self) -> Optional[str]:
        """Get decrypted phone number"""
        if not self._phone_number:
            return None
        try:
            return encryption_service.decrypt_string(self._phone_number)
        except Exception as e:
            logger.error(f"Decryption failed for phone number | BizID:{self.id} | Error:{e}")
            return None

    @phone_number.setter
    def phone_number(self, value: Optional[str]) -> None:
        """Set and encrypt phone number"""
        original_value = self._phone_number
        try:
            if value is None:
                self._phone_number = None
                return

            self._phone_number = encryption_service.encrypt_string(value)
            logger.info(f"Phone number updated | BizID:{self.id}")

        except Exception as e:
            self._phone_number = original_value
            logger.error(f"Phone number storage failed | BizID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("phone number") from e

    # SMTP Password management
    @property
    def smtp_password(self) -> Optional[str]:
        """Get decrypted SMTP password"""
        if not self._smtp_password:
            return None
        
        try:
            return encryption_service.decrypt_string(self._smtp_password)
        except Exception as e:
            logger.error(f"Decryption failed for SMTP password | BizID:{self.id} | Error:{e}")
            return None

    @smtp_password.setter
    def smtp_password(self, value: Optional[str]) -> None:
        """Set and encrypt SMTP password"""
        original_value = self._smtp_password
        try:
            if value is None:
                self._smtp_password = None
                return

            # Only enforce length requirement if strict validation is enabled
            if settings.should_validate('format') and len(value) < 8:
                logger.warning(f"SMTP password too short | BizID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                
                if settings.STRICT_VALIDATION:
                    raise InvalidConfigurationError("SMTP", "Password must be at least 8 characters")
                # If not strict, continue despite validation failure

            self._smtp_password = encryption_service.encrypt_string(value)
            logger.info(f"SMTP password updated | BizID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._smtp_password = original_value
            logger.error(f"SMTP password storage failed | BizID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("SMTP password") from e

    # Twilio Auth Token management
    @property
    def twilio_auth_token(self) -> Optional[str]:
        """Get decrypted Twilio auth token"""
        if not self._twilio_auth_token:
            return None
        
        try:
            return encryption_service.decrypt_string(self._twilio_auth_token)
        except Exception as e:
            logger.error(f"Decryption failed for Twilio token | BizID:{self.id} | Error:{e}")
            return None

    @twilio_auth_token.setter
    def twilio_auth_token(self, value: Optional[str]) -> None:
        """Set and encrypt Twilio auth token with validation"""
        original_value = self._twilio_auth_token
        try:
            if value is None:
                self._twilio_auth_token = None
                return

            # Only validate format if strict validation is enabled
            if settings.should_validate('format'):
                if len(value) != 32 or not value.startswith('SK'):
                    # Log the validation issue even if we bypass
                    logger.warning(f"Twilio token format invalid | BizID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                    
                    if settings.STRICT_VALIDATION:
                        raise InvalidConfigurationError(
                            "Twilio", 
                            "Auth token must be 32 characters starting with 'SK'"
                        )
                    # If not strict, continue despite validation failure
            
            # Always encrypt, even if validation is bypassed
            self._twilio_auth_token = encryption_service.encrypt_string(value)
            logger.info(f"Twilio token updated | BizID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._twilio_auth_token = original_value
            logger.error(f"Twilio token storage failed | BizID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("Twilio auth token") from e

    # WhatsApp API Key management                       *******CONTROLLARE documentazione specifica del provider WhatsApp*******
    @property
    def whatsapp_api_key(self) -> Optional[str]:
        """Get decrypted WhatsApp API key"""
        if not self._whatsapp_api_key:
            return None
        
        try:
            return encryption_service.decrypt_string(self._whatsapp_api_key)
        except Exception as e:
            logger.error(f"Decryption failed for WhatsApp API key | BizID:{self.id} | Error:{e}")
            return None

    @whatsapp_api_key.setter
    def whatsapp_api_key(self, value: Optional[str]) -> None:
        """Set and encrypt WhatsApp API key"""
        original_value = self._whatsapp_api_key
        try:
            if value is None:
                self._whatsapp_api_key = None
                return

            # Only enforce length requirement if strict validation is enabled
            if settings.should_validate('format') and len(value) < 16:
                logger.warning(f"WhatsApp API key too short | BizID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                
                if settings.STRICT_VALIDATION:
                    raise InvalidConfigurationError("WhatsApp", "API key must be at least 16 characters")
                # If not strict, continue despite validation failure

            self._whatsapp_api_key = encryption_service.encrypt_string(value)
            logger.info(f"WhatsApp API key updated | BizID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._whatsapp_api_key = original_value
            logger.error(f"WhatsApp key storage failed | BizID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("WhatsApp API key") from e