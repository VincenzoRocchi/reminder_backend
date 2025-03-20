"""
Modulo di configurazione centralizzata dell'applicazione.

Questo modulo definisce tutte le impostazioni necessarie per l'applicazione,
gestendo diversi ambienti (sviluppo, produzione) tramite variabili d'ambiente
e file .env specifici per ogni ambiente.

La classe Settings utilizza Pydantic per la validazione e la gestione di tutte
le configurazioni dell'applicazione.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, SecretStr, field_validator, model_validator, ConfigDict
import os
from pathlib import Path
from dotenv import load_dotenv

# ======================================================================
        # DETERMINAZIONE DELL'AMBIENTE E CARICAMENTO FILE .ENV
# ======================================================================

# Determina l'ambiente dal valore ENV (default: "development")
# Questo permette di cambiare facilmente ambiente usando una variabile d'ambiente
ENV = os.getenv("ENV", "development")

# Cerca il file .env specifico per l'ambiente (es: .env.development, .env.production)
env_file = f".env.{ENV}"
if Path(env_file).exists():
    # Se esiste il file specifico per l'ambiente, lo carica
    load_dotenv(env_file)
else:
    # Se non esiste il file specifico per l'ambiente, carica il file .env generico
    load_dotenv()


class Settings(BaseSettings):
    """
    Classe principale per la gestione delle impostazioni dell'applicazione.
    
    Definisce tutte le configurazioni necessarie per:
    - API (prefissi, versioni)
    - Database (connessione, pool)
    - Sicurezza (chiavi, token)
    - Servizi di notifica (email, SMS, WhatsApp)
    - Sistemi di pagamento (Stripe)
    - Storage (locale, S3)
    - Ambienti (development, production)
    
    Utilizza Pydantic per validare automaticamente tutte le impostazioni.
    """
    
    # ======================================================================
                            # IMPOSTAZIONI API
    # ======================================================================
    API_V1_STR: str = Field(
        default="/api/v1",
        description="Prefisso per le API v1"
    )
    
    PROJECT_NAME: str = Field(
        default="Reminder App API",
        description="Nome del progetto"
    )
    
    # ======================================================================
                            # IMPOSTAZIONI DATABASE
    # ======================================================================
    # Parametri di connessione al database MySQL
    DB_HOST: str = Field(
        default=os.getenv("DB_HOST", "localhost"),
        description="Host del database"
    )
    
    DB_PORT: int = Field(
        default=int(os.getenv("DB_PORT", "3306")),
        description="Porta MySQL standard"
    )
    
    DB_USER: str = Field(
        default=os.getenv("DB_USER", "root"),
        description="Utente del database"
    )
    
    DB_PASSWORD: str = Field(
        default=os.getenv("DB_PASSWORD", "password"),
        description="Password del database"
    )
    
    DB_NAME: str = Field(
        default=os.getenv("DB_NAME", "reminder_app"),
        description="Nome del database"
    )
    
    # Configurazione del pool di connessioni per migliorare le prestazioni
    DB_POOL_SIZE: int = Field(
        default=int(os.getenv("DB_POOL_SIZE", "5")),
        description="Dimensione iniziale del pool"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        description="Connessioni aggiuntive quando il pool è pieno"
    )
    
    DB_POOL_TIMEOUT: int = Field(
        default=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        description="Timeout in secondi per ottenere una connessione"
    )
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Costruisce la stringa di connessione al database.
        
        In ambiente di produzione aggiunge il parametro SSL per una connessione sicura.
        
        Returns:
            str: Stringa di connessione completa per SQLAlchemy
        """
        uri = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        if not self.IS_DEVELOPMENT:
            # Aggiunge SSL per ambienti di produzione/staging
            uri += "?ssl=true"
        return uri
    
    # ======================================================================
                            # IMPOSTAZIONI SICUREZZA
    # ======================================================================
    # Chiave segreta per la firma dei token JWT
    SECRET_KEY: str = Field(
        default=os.getenv("SECRET_KEY", "your-secret-key-here"),
        description="Chiave segreta per la firma dei token JWT"
    )
    
    # Algoritmo usato per la firma dei token JWT
    ALGORITHM: str = Field(
        default=os.getenv("ALGORITHM", "HS256"),
        description="Algoritmo usato per la firma dei token JWT"
    )
    
    # Prefisso per l'header Authorization
    JWT_TOKEN_PREFIX: str = Field(
        default=os.getenv("JWT_TOKEN_PREFIX", "Bearer"),
        description="Prefisso per l'header Authorization"
    )
    
    # Tempi di scadenza dei token
    # Durata del token di accesso (in minuti)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        description="Durata del token di accesso (in minuti)"
    )
    
    # Durata del token di refresh (in giorni)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        description="Durata del token di refresh (in giorni)"
    )
    
    # Durata del token di reset password (in minuti)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "15")),
        description="Durata del token di reset password (in minuti)"
    )
    
    # ======================================================================
                            # IMPOSTAZIONI EMAIL
    # ======================================================================
    # Configurazione server SMTP per l'invio di email
    SMTP_HOST: str = Field(
        default=os.getenv("SMTP_HOST", ""),
        description="Host del server SMTP"
    )
    
    SMTP_PORT: int = Field(
        default=int(os.getenv("SMTP_PORT", "587")),
        description="Porta SMTP (587 per TLS)"
    )
    
    SMTP_USER: str = Field(
        default=os.getenv("SMTP_USER", ""),
        description="Username SMTP"
    )
    
    SMTP_PASSWORD: str = Field(
        default=os.getenv("SMTP_PASSWORD", ""),
        description="Password SMTP"
    )
    
    EMAIL_FROM: str = Field(
        default=os.getenv("EMAIL_FROM", "noreply@reminderapp.com"),
        description="Indirizzo mittente"
    )
    
    # ======================================================================
                            # IMPOSTAZIONI SMS (TWILIO)
    # ======================================================================
    # Credenziali Twilio per l'invio di SMS
    TWILIO_ACCOUNT_SID: str = Field(
        default=os.getenv("TWILIO_ACCOUNT_SID", ""),
        description="SID account Twilio"
    )
    
    TWILIO_AUTH_TOKEN: str = Field(
        default=os.getenv("TWILIO_AUTH_TOKEN", ""),
        description="Token di autenticazione Twilio"
    )
    
    TWILIO_PHONE_NUMBER: str = Field(
        default=os.getenv("TWILIO_PHONE_NUMBER", ""),
        description="Numero di telefono Twilio"
    )
    
    # ======================================================================
                            # IMPOSTAZIONI WHATSAPP
    # ======================================================================
    # Credenziali per API WhatsApp Business
    WHATSAPP_API_KEY: str = Field(
        default=os.getenv("WHATSAPP_API_KEY", ""),
        description="Chiave API WhatsApp"
    )
    
    WHATSAPP_API_URL: str = Field(
        default=os.getenv("WHATSAPP_API_URL", ""),
        description="URL endpoint API WhatsApp"
    )
    
    # ======================================================================
                    # IMPOSTAZIONI STRIPE (GATEWAY PAGAMENTI)
    # ======================================================================
    # Credenziali Stripe per processare i pagamenti
    STRIPE_API_KEY: str = Field(
        default=os.getenv("STRIPE_API_KEY", ""),
        description="Chiave API Stripe"
    )
    
    STRIPE_WEBHOOK_SECRET: str = Field(
        default=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        description="Segreto webhook Stripe"
    )
    
    @property
    def PAYMENT_SUCCESS_URL(self) -> str:
        """
        URL di reindirizzamento dopo un pagamento riuscito.
        
        Cambia automaticamente in base all'ambiente (sviluppo o produzione).
        
        Returns:
            str: URL completo per il reindirizzamento
        """
        return os.getenv("PAYMENT_SUCCESS_URL", 
            "http://localhost:3000/payment/success" if self.IS_DEVELOPMENT else 
            "https://your-production-domain.com/payment/success"
        )
    
    @property
    def PAYMENT_CANCEL_URL(self) -> str:
        """
        URL di reindirizzamento dopo un pagamento annullato.
        
        Cambia automaticamente in base all'ambiente (sviluppo o produzione).
        
        Returns:
            str: URL completo per il reindirizzamento
        """
        return os.getenv("PAYMENT_CANCEL_URL", 
            "http://localhost:3000/payment/cancel" if self.IS_DEVELOPMENT else 
            "https://your-production-domain.com/payment/cancel"
        )

    # ======================================================================
                            # IMPOSTAZIONI AMBIENTE
    # ======================================================================
    # Ambiente corrente (development, testing, production)
    ENV: str = Field(
        default=ENV,
        description="Ambiente corrente (development, testing, production)"
    )
    
    @property
    def IS_DEVELOPMENT(self) -> bool:
        """
        Verifica se l'applicazione è in ambiente di sviluppo.
        
        Returns:
            bool: True se l'ambiente è 'development', False altrimenti
        """
        return self.ENV == "development"

    @property
    def IS_PRODUCTION(self) -> bool:
        """
        Verifica se l'applicazione è in ambiente di produzione.
        
        Returns:
            bool: True se l'ambiente è 'production', False altrimenti
        """
        return self.ENV == "production"
    
    STRICT_VALIDATION: bool = Field(
        default=os.getenv("STRICT_VALIDATION", "True" if not ENV == "development" else "False").lower() == "true",
        description="Enforce strict validation of sensitive data (default: True in production, False in development)"
    )

    def should_validate(self, validation_type: str = "all") -> bool:
        """
        Determina se un particolare tipo di validazione deve essere applicato in base alle impostazioni dell'ambiente.
        
        Args:
            validation_type: Tipo di validazione da controllare (es. 'security', 'format', 'all')
            
        Returns:
            bool: True se la validazione deve essere applicata, False se può essere bypassata
        """
        # Valida sempre in produzione indipendentemente dall'impostazione STRICT_VALIDATION
        if self.IS_PRODUCTION:
            return True
            
        # In sviluppo, rispetta l'impostazione STRICT_VALIDATION
        return self.STRICT_VALIDATION


    # ======================================================================
                            # IMPOSTAZIONI LOGGING
    # ======================================================================
    # Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO"),
        description="Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Formato dei messaggi di log
    LOG_FORMAT: str = Field(
        default=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        description="Formato dei messaggi di log"
    )

    # ======================================================================
                            # IMPOSTAZIONI CORS
    # ======================================================================
    # Origini permesse per le richieste CORS (separate da virgola)
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
        ],
        description="Origini permesse per le richieste CORS (separate da virgola)"
    )
    
    # Abilita l'invio di credenziali nelle richieste CORS
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true",
        description="Abilita l'invio di credenziali nelle richieste CORS"
    )
    
    # ======================================================================
                            # IMPOSTAZIONI SCHEDULER
    # ======================================================================
    # Fuso orario per lo scheduler (default: UTC)
    SCHEDULER_TIMEZONE: str = Field(
        default=os.getenv("SCHEDULER_TIMEZONE", "UTC"),
        description="Fuso orario per lo scheduler (default: UTC)"
    )
    
    # ======================================================================
                            # SICUREZZA COOKIE
    # ======================================================================
    @property
    def SECURE_COOKIES(self) -> bool:
        """
        Determina se i cookie devono avere il flag 'secure'.
        
        In sviluppo è di solito False per permettere HTTP,
        in produzione è True per richiedere HTTPS.
        
        Returns:
            bool: True se i cookie devono essere sicuri, False altrimenti
        """
        return os.getenv("SECURE_COOKIES", "False" if self.IS_DEVELOPMENT else "True").lower() == "true"
    
    # ======================================================================
                            # CONFIGURAZIONE STORAGE AWS S3
    # ======================================================================
    # Tipo di storage: 's3' per AWS S3, 'local' per filesystem locale
    STORAGE_TYPE: str = Field(
        default=os.getenv("STORAGE_TYPE", "local"),
        pattern=r"^(s3|local)$",
        description="Tipo di storage: 's3' per AWS S3, 'local' per filesystem locale"
    )
    
    # Nome del bucket S3 (obbligatorio se STORAGE_TYPE è 's3')
    S3_BUCKET_NAME: Optional[str] = Field(
        default=os.getenv("S3_BUCKET_NAME"),
        min_length=3,
        pattern=r"^[a-z0-9.-]{3,63}$",
        examples=["my-production-bucket"],
        description="Nome del bucket S3 (obbligatorio se STORAGE_TYPE è 's3')"
    )
    
    # Chiave di accesso per AWS S3 (obbligatoria se STORAGE_TYPE è 's3')
    S3_ACCESS_KEY: Optional[SecretStr] = Field(
        default=SecretStr(os.getenv("S3_ACCESS_KEY", "")) if os.getenv("S3_ACCESS_KEY") else None,
        min_length=20,
        description="Chiave di accesso per AWS S3 (obbligatoria se STORAGE_TYPE è 's3')"
    )
    
    # Chiave segreta per AWS S3 (obbligatoria se STORAGE_TYPE è 's3')
    S3_SECRET_KEY: Optional[SecretStr] = Field(
        default=SecretStr(os.getenv("S3_SECRET_KEY", "")) if os.getenv("S3_SECRET_KEY") else None,
        min_length=40,
        description="Chiave segreta per AWS S3 (obbligatoria se STORAGE_TYPE è 's3')"
    )
    
    # Regione AWS per il bucket S3 (obbligatoria se STORAGE_TYPE è 's3')
    S3_REGION: Optional[str] = Field(
        default=os.getenv("S3_REGION"),
        pattern=r"^[a-z]{2}-[a-z]+-\d$",
        examples=["us-east-1"],
        description="Regione AWS per il bucket S3 (obbligatoria se STORAGE_TYPE è 's3')"
    )
    
    # Tipo di ACL per gli oggetti S3 (private o public-read)
    S3_OBJECT_ACL: str = Field(
        default=os.getenv("S3_OBJECT_ACL", "private"),
        pattern=r"^(private|public-read)$",
        description="Tipo di ACL per gli oggetti S3 (private o public-read)"
    )
    
    # ======================================================================
                            # RATE LIMITING
    # ======================================================================
    # Abilita o disabilita il rate limiting sulle API
    RATE_LIMIT_ENABLED: bool = Field(
        default=os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true",
        description="Abilita o disabilita il rate limiting sulle API"
    )
    
    # Limite di default (formato: "numero/unità" es. "100/minute")
    DEFAULT_RATE_LIMIT: str = Field(
        default=os.getenv("DEFAULT_RATE_LIMIT", "100/minute"),
        description="Limite di default (formato: \"numero/unità\" es. \"100/minute\")"
    )

    # ======================================================================
                            # DOCUMENTAZIONE API
    # ======================================================================
    # URL per la documentazione Swagger UI
    DOCS_URL: str = Field(
        default=os.getenv("DOCS_URL", "/docs"),
        description="URL per la documentazione Swagger UI"
    )
    
    # URL per la documentazione ReDoc
    REDOC_URL: str = Field(
        default=os.getenv("REDOC_URL", "/redoc"),
        description="URL per la documentazione ReDoc"
    )
    
    # URL per il file OpenAPI JSON
    OPENAPI_URL: str = Field(
        default=os.getenv("OPENAPI_URL", "/openapi.json"),
        description="URL per il file OpenAPI JSON"
    )
    
    # ======================================================================
                            # CONFIGURAZIONE PYDANTIC
    # ======================================================================
    # Configurazione del modello Pydantic
    model_config = ConfigDict(
        env_file=env_file,  # File .env da cui caricare le variabili
        env_file_encoding="utf-8",  # Codifica del file .env
        case_sensitive=True,  # I nomi delle variabili sono case-sensitive
        validate_assignment=True,  # Validazione anche dopo l'assegnazione
        extra="forbid"  # Vieta campi extra non definiti nel modello
    )

    # ======================================================================
                            # VALIDATORI
    # ======================================================================
    @field_validator("STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        """
        Validatore per il tipo di storage.
        
        Accetta solo 's3' o 'local' come valori validi.
        
        Args:
            v: Valore da validare
            
        Returns:
            str: Valore validato
            
        Raises:
            ValueError: Se il valore non è valido
        """
        if v not in {"s3", "local"}:
            raise ValueError("Storage type must be 's3' or 'local'")
        return v

    @model_validator(mode="after")
    def validate_s3_config(self) -> "Settings":
        """
        Validatore per la configurazione S3.
        
        Se STORAGE_TYPE è 's3', verifica che tutte le impostazioni S3 necessarie
        siano state fornite e che il nome del bucket sia valido.
        
        Returns:
            Settings: Istanza di Settings validata
            
        Raises:
            ValueError: Se la configurazione S3 non è valida
        """
        if self.STORAGE_TYPE == "s3":
            # Verifica che tutte le impostazioni S3 necessarie siano presenti
            missing = []
            if not self.S3_BUCKET_NAME:
                missing.append("S3_BUCKET_NAME")
            if not self.S3_ACCESS_KEY:
                missing.append("S3_ACCESS_KEY")
            if not self.S3_SECRET_KEY:
                missing.append("S3_SECRET_KEY")
            if not self.S3_REGION:
                missing.append("S3_REGION")
            
            if missing:
                raise ValueError(
                    f"Missing required S3 configuration for storage type 's3': {', '.join(missing)}"
                )
                
            # Validazione formato del nome del bucket
            if self.S3_BUCKET_NAME and (".." in self.S3_BUCKET_NAME or self.S3_BUCKET_NAME.startswith("-")):
                raise ValueError("Invalid S3 bucket name format")
        
        return self

    @property
    def s3_credentials_provided(self) -> bool:
        """
        Verifica se tutte le credenziali S3 necessarie sono disponibili.
        
        Returns:
            bool: True se tutte le credenziali S3 sono disponibili, False altrimenti
        """
        return all([
            self.S3_ACCESS_KEY,
            self.S3_SECRET_KEY,
            self.S3_REGION,
            self.S3_BUCKET_NAME
        ])
    
    def validate_settings(self) -> None:
        """
        Valida che le impostazioni critiche siano configurate correttamente.
        
        In produzione, verifica che:
        - SECRET_KEY sia impostata e sufficientemente lunga
        - DB_HOST non sia localhost
        - Le impostazioni SMTP siano complete se una di esse è specificata
        
        Raises:
            AssertionError: Se una validazione fallisce
        """
        if self.IS_PRODUCTION:
            # Configurazioni essenziali per la produzione
            assert self.SECRET_KEY != "your-secret-key-here", "Production SECRET_KEY must be set"
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY should be at least 32 characters in production"
            
            # Validazione database
            assert self.DB_HOST != "localhost", "Production DB_HOST should not be localhost"
            
            # Validazione email se necessaria
            if any([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]):
                assert all([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]), "SMTP settings incomplete"


# ======================================================================
                # INIZIALIZZAZIONE DELLE IMPOSTAZIONI
# ======================================================================

# Crea l'istanza delle impostazioni
settings = Settings()

# Se in produzione, valida le impostazioni critiche
if settings.IS_PRODUCTION:
    settings.validate_settings()