"""Initial migration

Revision ID: bfdb78bee16c
Revises: 
Create Date: 2025-03-26 12:34:56.789012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfdb78bee16c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creazione delle tabelle iniziali - Modificata per SQLite."""
    # Per SQLite, invece di modificare tabelle esistenti, creiamo tutte le tabelle da zero
    
    # Creiamo la tabella users (se non esiste)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    
    # Creazione della tabella clients
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clients_id', 'clients', ['id'], unique=False)
    
    # Creazione della tabella service_accounts
    op.create_table('service_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', name='servicetypeenum'), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('smtp_host', sa.String(length=255), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('smtp_user', sa.String(length=255), nullable=True),
        sa.Column('smtp_password', sa.String(length=500), nullable=True),
        sa.Column('email_from', sa.String(length=255), nullable=True),
        sa.Column('twilio_account_sid', sa.String(length=255), nullable=True),
        sa.Column('twilio_auth_token', sa.String(length=500), nullable=True),
        sa.Column('twilio_phone_number', sa.String(length=20), nullable=True),
        sa.Column('whatsapp_api_key', sa.String(length=500), nullable=True),
        sa.Column('whatsapp_api_url', sa.String(length=255), nullable=True),
        sa.Column('whatsapp_phone_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_service_accounts_id', 'service_accounts', ['id'], unique=False)
    
    # Creazione della tabella reminders
    op.create_table('reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reminder_type', sa.Enum('PAYMENT', 'DEADLINE', 'NOTIFICATION', name='remindertypeenum'), nullable=False),
        sa.Column('notification_type', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', name='notification_type_enum'), nullable=False),
        sa.Column('service_account_id', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_pattern', sa.String(length=255), nullable=True),
        sa.Column('reminder_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reminders_id', 'reminders', ['id'], unique=False)
    
    # Creazione della tabella notifications
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reminder_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('notification_type', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', name='notification_type_enum'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'CANCELLED', name='notificationstatusenum'), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    
    # Creazione della tabella reminder_recipients
    op.create_table('reminder_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reminder_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reminder_id', 'client_id', name='unique_reminder_client')
    )
    op.create_index('ix_reminder_recipients_id', 'reminder_recipients', ['id'], unique=False)


def downgrade() -> None:
    """Eliminate all tables."""
    # Drop tables in reverse order of dependencies
    op.drop_index('ix_reminder_recipients_id', table_name='reminder_recipients')
    op.drop_table('reminder_recipients')
    
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index('ix_reminders_id', table_name='reminders')
    op.drop_table('reminders')
    
    op.drop_index('ix_service_accounts_id', table_name='service_accounts')
    op.drop_table('service_accounts')
    
    op.drop_index('ix_clients_id', table_name='clients')
    op.drop_table('clients')
    
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')