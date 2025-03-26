"""Initial database migration

Revision ID: 0001
Revises: 
Create Date: 2024-03-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create sender_identities table
    op.create_table('sender_identities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create email_configurations table
    op.create_table('email_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('smtp_server', sa.String(length=255), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False),
        sa.Column('smtp_username', sa.String(length=255), nullable=False),
        sa.Column('smtp_password', sa.String(length=255), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=True),
        sa.Column('use_tls', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create clients table
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reminders table
    op.create_table('reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reminder_type', sa.Enum('PAYMENT', 'DEADLINE', 'NOTIFICATION', name='remindertypeenum'), nullable=False),
        sa.Column('notification_type', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', name='notificationtypeenum'), nullable=False),
        sa.Column('email_configuration_id', sa.Integer(), nullable=True),
        sa.Column('sender_identity_id', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_pattern', sa.String(length=255), nullable=True),
        sa.Column('reminder_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['email_configuration_id'], ['email_configurations.id'], ),
        sa.ForeignKeyConstraint(['sender_identity_id'], ['sender_identities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reminder_recipients table
    op.create_table('reminder_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reminder_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reminder_id', 'client_id', name='unique_reminder_client')
    )
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reminder_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'DELIVERED', 'READ', name='notificationstatusenum'), nullable=False),
        sa.Column('notification_type', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', name='notificationtypeenum'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_clients_email'), 'clients', ['email'], unique=False)
    op.create_index(op.f('ix_clients_user_id'), 'clients', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_configurations_user_id'), 'email_configurations', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_client_id'), 'notifications', ['client_id'], unique=False)
    op.create_index(op.f('ix_notifications_reminder_id'), 'notifications', ['reminder_id'], unique=False)
    op.create_index(op.f('ix_reminder_recipients_client_id'), 'reminder_recipients', ['client_id'], unique=False)
    op.create_index(op.f('ix_reminder_recipients_reminder_id'), 'reminder_recipients', ['reminder_id'], unique=False)
    op.create_index(op.f('ix_reminders_email_configuration_id'), 'reminders', ['email_configuration_id'], unique=False)
    op.create_index(op.f('ix_reminders_reminder_date'), 'reminders', ['reminder_date'], unique=False)
    op.create_index(op.f('ix_reminders_user_id'), 'reminders', ['user_id'], unique=False)
    op.create_index(op.f('ix_sender_identities_user_id'), 'sender_identities', ['user_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade():
    # Drop all tables in reverse order
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_sender_identities_user_id'), table_name='sender_identities')
    op.drop_index(op.f('ix_reminders_user_id'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_reminder_date'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_email_configuration_id'), table_name='reminders')
    op.drop_index(op.f('ix_reminder_recipients_reminder_id'), table_name='reminder_recipients')
    op.drop_index(op.f('ix_reminder_recipients_client_id'), table_name='reminder_recipients')
    op.drop_index(op.f('ix_notifications_reminder_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_client_id'), table_name='notifications')
    op.drop_index(op.f('ix_email_configurations_user_id'), table_name='email_configurations')
    op.drop_index(op.f('ix_clients_user_id'), table_name='clients')
    op.drop_index(op.f('ix_clients_email'), table_name='clients')
    
    op.drop_table('notifications')
    op.drop_table('reminder_recipients')
    op.drop_table('reminders')
    op.drop_table('clients')
    op.drop_table('email_configurations')
    op.drop_table('sender_identities')
    op.drop_table('users') 