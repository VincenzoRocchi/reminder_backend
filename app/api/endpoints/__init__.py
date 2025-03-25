# app/api/endpoints/__init__.py
from .auth import router as auth_router
from .users import router as users_router
from .businesses import router as businesses_router
from .clients import router as clients_router
from .reminders import router as reminders_router
from .notifications import router as notifications_router
from .serviceAccounts import router as service_accounts_router