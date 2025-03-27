# app/api/endpoints/__init__.py
from .auth import router as auth_router
from .users import router as users_router
from .clients import router as clients_router
from .reminders import router as reminders_router
from .notifications import router as notifications_router
from .emailConfigurations import router as service_accounts_router
from .senderIdentities import router as sender_identities_router
from .emailConfigurations import router as email_configurations_router