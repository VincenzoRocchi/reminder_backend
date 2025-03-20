"""
Pacchetto core dell'applicazione.

Questo pacchetto contiene tutti i moduli fondamentali per il funzionamento
dell'applicazione, inclusi:

- settings.py: Configurazione dell'applicazione
- security.py: Gestione della sicurezza e crittografia
- auth.py: Autenticazione e autorizzazione
- permissions.py: Controllo degli accessi basato sui ruoli
- encryption.py: Crittografia dei dati sensibili
- config.py: Configurazione generale dell'applicazione

L'importazione di 'settings' qui rende le impostazioni disponibili
a tutti i moduli che importano il pacchetto core.
"""
# Importa le impostazioni per renderle disponibili tramite import dal pacchetto core
# Esempio: from app.core import settings
from app.core.settings import settings

# Importa i moduli fondamentali