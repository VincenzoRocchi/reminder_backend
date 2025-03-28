"""Update sender identity schema

Revision ID: 20240601_update_sender_identity
Revises: initial_migration
Create Date: 2024-06-01

This migration updates the sender_identities table to split the value field into email
and phone_number fields, and adds the email_configuration_id field. It also makes
sender_identity_id a required field in reminders and adds it to notifications.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models.senderIdentities import IdentityTypeEnum

# revision identifiers, used by Alembic
revision = '20240601_update_sender_identity'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Add WhatsApp to the identity type enum
    op.execute("ALTER TYPE identitytypeenum ADD VALUE 'WHATSAPP' IF NOT EXISTS")
    
    # Add new columns to sender_identities table
    op.add_column('sender_identities', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('sender_identities', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('sender_identities', sa.Column('email_configuration_id', sa.Integer(), nullable=True))
    
    # Create foreign key for email_configuration_id
    op.create_foreign_key(
        'fk_sender_identity_email_config',
        'sender_identities', 'email_configurations',
        ['email_configuration_id'], ['id']
    )
    
    # Copy data from value to email or phone_number based on identity_type
    op.execute("""
        UPDATE sender_identities
        SET email = value
        WHERE identity_type = 'EMAIL'
    """)
    
    op.execute("""
        UPDATE sender_identities
        SET phone_number = value
        WHERE identity_type = 'PHONE'
    """)
    
    # Add sender_identity_id to notifications table
    op.add_column('notifications', sa.Column('sender_identity_id', sa.Integer(), nullable=True))
    
    # Create foreign key for sender_identity_id in notifications
    op.create_foreign_key(
        'fk_notification_sender_identity',
        'notifications', 'sender_identities',
        ['sender_identity_id'], ['id']
    )
    
    # Fill sender_identity_id in notifications with the sender identity 
    # from the related reminder
    op.execute("""
        UPDATE notifications n
        SET sender_identity_id = r.sender_identity_id
        FROM reminders r
        WHERE n.reminder_id = r.id AND r.sender_identity_id IS NOT NULL
    """)
    
    # Make sender_identity_id NOT NULL in reminders
    op.execute("""
        ALTER TABLE reminders 
        ALTER COLUMN sender_identity_id SET NOT NULL
    """)
    
    # Make sender_identity_id NOT NULL in notifications
    op.execute("""
        ALTER TABLE notifications 
        ALTER COLUMN sender_identity_id SET NOT NULL
    """)
    
    # Update notification_type to use the new enum from reminders.py
    op.execute("""
        ALTER TABLE notifications
        ALTER COLUMN notification_type TYPE VARCHAR(255)
    """)
    
    op.execute("""
        DROP TYPE IF EXISTS notification_type_enum
    """)
    
    op.execute("""
        ALTER TABLE notifications
        ALTER COLUMN notification_type TYPE notificationtypeenum USING notification_type::notificationtypeenum
    """)
    
    # Drop the value column (only after data is migrated)
    op.drop_column('sender_identities', 'value')

def downgrade():
    # Add value column back to sender_identities
    op.add_column('sender_identities', sa.Column('value', sa.String(255), nullable=True))
    
    # Copy data back to value from email or phone_number
    op.execute("""
        UPDATE sender_identities
        SET value = email
        WHERE identity_type = 'EMAIL'
    """)
    
    op.execute("""
        UPDATE sender_identities
        SET value = phone_number
        WHERE identity_type = 'PHONE' OR identity_type = 'WHATSAPP'
    """)
    
    # Make value NOT NULL
    op.execute("""
        ALTER TABLE sender_identities
        ALTER COLUMN value SET NOT NULL
    """)
    
    # Remove the constraint that sender_identity_id must be NOT NULL in reminders
    op.execute("""
        ALTER TABLE reminders
        ALTER COLUMN sender_identity_id DROP NOT NULL
    """)
    
    # Drop sender_identity_id from notifications
    op.drop_constraint('fk_notification_sender_identity', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'sender_identity_id')
    
    # Drop new columns from sender_identities
    op.drop_constraint('fk_sender_identity_email_config', 'sender_identities', type_='foreignkey')
    op.drop_column('sender_identities', 'email_configuration_id')
    op.drop_column('sender_identities', 'phone_number')
    op.drop_column('sender_identities', 'email')
    
    # Create notification_type_enum and convert back
    op.execute("""
        CREATE TYPE notification_type_enum AS ENUM ('EMAIL', 'SMS', 'WHATSAPP')
    """)
    
    op.execute("""
        ALTER TABLE notifications
        ALTER COLUMN notification_type TYPE VARCHAR(255)
    """)
    
    op.execute("""
        ALTER TABLE notifications
        ALTER COLUMN notification_type TYPE notification_type_enum USING notification_type::notification_type_enum
    """) 