# app/schemas/__init__.py
from .user import User, UserCreate, UserUpdate
from .clients import Client, ClientCreate, ClientUpdate
from .reminders import Reminder, ReminderCreate, ReminderUpdate
from .emailConfigurations import EmailConfiguration, EmailConfigurationCreate, EmailConfigurationUpdate
from .notifications import Notification, NotificationCreate, NotificationUpdate
from .token import Token, TokenPayload
from .senderIdentities import SenderIdentity, SenderIdentityCreate, SenderIdentityUpdate