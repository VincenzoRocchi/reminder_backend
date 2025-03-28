# Guida al Deployment in Produzione

## Panoramica

I tuoi file attuali rappresentano una solida base di partenza. Le modifiche in produzione riguarderanno principalmente il file di configurazione (`settings`), le configurazioni di deploy e la gestione dei servizi (database, autenticazione, logging). **Non saranno necessarie modifiche alla logica di base dei modelli, schemi ed endpoint.**

## Componenti Principali

### 1. Modelli (models)

- Usa `business.py` come riferimento.
- In produzione, verifica indici, constraint e performance.
- Configura l'`encryption_service` con chiavi sicure.

### 2. Schemi (schemas)

- Usa `business.py` in schemas come modello.
- In produzione, assicurati che i validator siano stringenti e che i dati sensibili siano gestiti in modo sicuro.
- Utilizza questi schemi per validare input e serializzare output, mantenendo una struttura coerente.

### 3. Endpoint (endpoints)

- Usa `businesses.py` come riferimento.
- In produzione, implementa un'autenticazione robusta, gestisci errori e log, e configura correttamente le dipendenze (DB, sicurezza).
- Integra strumenti di monitoraggio e rate limiting.

## Sicurezza in Produzione

### Modifiche Specifiche per la Produzione

#### 1. Configurazione dell'Ambiente

- Imposta `ENV=production` nelle variabili d'ambiente.
- Imposta `STRICT_VALIDATION=True` per una validazione rigorosa dei dati.
- Configura una `SECRET_KEY` forte e unica (minimo 32 caratteri).
- Imposta `SECURE_COOKIES=true` per applicare cookie sicuri.

#### 2. Impostazioni CORS

- Aggiorna `CORS_ORIGINS` con domini specifici consentiti (senza caratteri jolly).
- Esempio: `CORS_ORIGINS=["https://yourapp.com", "https://admin.yourapp.com"]`.

#### 3. Configurazione SSL/TLS

- Assicurati che i certificati SSL siano configurati correttamente sul server.
- Configura il rinnovo automatico dei certificati.
- Configura cifrari e protocolli SSL adeguati (solo TLS 1.2+).

#### 4. Sicurezza dei Token

- Configura `ACCESS_TOKEN_EXPIRE_MINUTES` con un valore appropriato (ad esempio, 15-30 minuti).
- Imposta `REFRESH_TOKEN_EXPIRE_DAYS` a un valore ragionevole (ad esempio, 7-14 giorni).

#### 5. Limitazione del Tasso

- Abilita la limitazione del tasso impostando `RATE_LIMIT_ENABLED=true`.
- Configura limiti di tasso appropriati con `DEFAULT_RATE_LIMIT=60/minuto`.

#### 6. Blacklist dei Token (Implementazione Redis)

- Configura Redis per il blacklist dei token sostituendo `InMemoryTokenBlacklist` con `RedisTokenBlacklist`.
- Esempio di implementazione:

    ```python
    from app.core.token_blacklist import RedisTokenBlacklist
    token_blacklist = RedisTokenBlacklist(settings.REDIS_URL)
    ```

- Configura `REDIS_URL` nelle impostazioni dell'ambiente.

#### 7. Error Logging

- Set `LOG_LEVEL=INFO` for production (avoid DEBUG level in production).
- Configure proper logging forwarding to your monitoring solution.
- Ensure sensitive data is not logged.

## Storage

### Storage System Configuration

- Set `STORAGE_TYPE=s3` for AWS S3 storage.
- Configure all necessary credentials and settings for S3.
