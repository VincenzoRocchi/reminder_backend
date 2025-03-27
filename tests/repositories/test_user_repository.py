import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository, user_repository
from app.models.users import User
from app.schemas.user import UserCreate, UserUpdate


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        business_name="Test Business",
        phone_number=None,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    return user


def test_repository_singleton():
    """Test that user_repository is a singleton instance of UserRepository"""
    assert isinstance(user_repository, UserRepository)
    
    # Create a new instance and check that it's a separate object
    new_repository = UserRepository()
    assert new_repository is not user_repository


def test_get_by_id(db_session, test_user):
    """Test getting a user by ID"""
    # Get the user by ID
    retrieved_user = user_repository.get(db_session, id=test_user.id)
    
    # Check that the user was retrieved
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.username == test_user.username
    assert retrieved_user.email == test_user.email


def test_get_by_id_not_found(db_session):
    """Test getting a user by ID that doesn't exist"""
    # Get a non-existent user
    retrieved_user = user_repository.get(db_session, id=999)
    
    # Check that None was returned
    assert retrieved_user is None


def test_get_by_email(db_session, test_user):
    """Test getting a user by email"""
    # Get the user by email
    retrieved_user = user_repository.get_by_email(db_session, email=test_user.email)
    
    # Check that the user was retrieved
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.email == test_user.email


def test_get_by_email_not_found(db_session):
    """Test getting a user by email that doesn't exist"""
    # Get a non-existent user
    retrieved_user = user_repository.get_by_email(db_session, email="nonexistent@example.com")
    
    # Check that None was returned
    assert retrieved_user is None


def test_get_by_username(db_session, test_user):
    """Test getting a user by username"""
    # Get the user by username
    retrieved_user = user_repository.get_by_username(db_session, username=test_user.username)
    
    # Check that the user was retrieved
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.username == test_user.username


def test_get_by_username_not_found(db_session):
    """Test getting a user by username that doesn't exist"""
    # Get a non-existent user
    retrieved_user = user_repository.get_by_username(db_session, username="nonexistentuser")
    
    # Check that None was returned
    assert retrieved_user is None


def test_get_by_email_or_username(db_session, test_user):
    """Test getting a user by email or username"""
    # Get by email
    retrieved_user = user_repository.get_by_email_or_username(
        db_session, email=test_user.email
    )
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    
    # Get by username
    retrieved_user = user_repository.get_by_email_or_username(
        db_session, username=test_user.username
    )
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    
    # Get by both (should return user matching email)
    retrieved_user = user_repository.get_by_email_or_username(
        db_session, email=test_user.email, username="nonexistentuser"
    )
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    
    # Get with neither
    retrieved_user = user_repository.get_by_email_or_username(
        db_session, email=None, username=None
    )
    assert retrieved_user is None
    
    # Get non-existent user
    retrieved_user = user_repository.get_by_email_or_username(
        db_session, email="nonexistent@example.com", username="nonexistentuser"
    )
    assert retrieved_user is None


@patch('app.repositories.user.get_password_hash')
def test_create(mock_get_password_hash, db_session):
    """Test creating a user"""
    # Configure mock
    mock_get_password_hash.return_value = "hashed_test_password"
    
    # Create user schema
    user_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="test_password",
        first_name="New",
        last_name="User",
        business_name="New Business",
        phone_number="1234567890",
        is_active=True
    )
    
    # Create the user
    new_user = user_repository.create(db_session, obj_in=user_data)
    
    # Check that the password was hashed
    mock_get_password_hash.assert_called_once_with("test_password")
    
    # Check that the user was created with correct attributes
    assert new_user.id is not None
    assert new_user.username == "newuser"
    assert new_user.email == "newuser@example.com"
    assert new_user.hashed_password == "hashed_test_password"
    assert new_user.first_name == "New"
    assert new_user.last_name == "User"
    assert new_user.business_name == "New Business"
    
    # Check that the user can be retrieved from the database
    retrieved_user = db_session.query(User).filter_by(id=new_user.id).first()
    assert retrieved_user is not None
    assert retrieved_user.username == "newuser"


@patch('app.repositories.user.get_password_hash')
def test_update_with_password(mock_get_password_hash, db_session, test_user):
    """Test updating a user with password change"""
    # Configure mock
    mock_get_password_hash.return_value = "new_hashed_password"
    
    # Create update schema
    update_data = UserUpdate(
        first_name="Updated",
        last_name="Name",
        password="new_password"
    )
    
    # Update the user
    updated_user = user_repository.update(db_session, db_obj=test_user, obj_in=update_data)
    
    # Check that the password was hashed
    mock_get_password_hash.assert_called_once_with("new_password")
    
    # Check that the user was updated with correct attributes
    assert updated_user.id == test_user.id
    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.hashed_password == "new_hashed_password"
    assert updated_user.username == test_user.username  # Unchanged
    assert updated_user.email == test_user.email  # Unchanged


def test_update_without_password(db_session, test_user):
    """Test updating a user without password change"""
    # Create update schema
    update_data = UserUpdate(
        first_name="Updated",
        last_name="Name",
        business_name="Updated Business"
    )
    
    # Update the user
    updated_user = user_repository.update(db_session, db_obj=test_user, obj_in=update_data)
    
    # Check that the user was updated with correct attributes
    assert updated_user.id == test_user.id
    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.business_name == "Updated Business"
    assert updated_user.hashed_password == test_user.hashed_password  # Unchanged


def test_update_with_dict(db_session, test_user):
    """Test updating a user with a dictionary instead of schema"""
    # Create update dict
    update_data = {
        "first_name": "Dict",
        "last_name": "Update",
        "business_name": "Dict Business"
    }
    
    # Update the user
    updated_user = user_repository.update(db_session, db_obj=test_user, obj_in=update_data)
    
    # Check that the user was updated with correct attributes
    assert updated_user.id == test_user.id
    assert updated_user.first_name == "Dict"
    assert updated_user.last_name == "Update"
    assert updated_user.business_name == "Dict Business"


def test_delete(db_session, test_user):
    """Test deleting a user"""
    # Delete the user
    deleted_user = user_repository.remove(db_session, id=test_user.id)
    
    # Check that the correct user was returned
    assert deleted_user.id == test_user.id
    
    # Check that the user was deleted from the database
    retrieved_user = db_session.query(User).filter_by(id=test_user.id).first()
    assert retrieved_user is None


def test_get_multi(db_session):
    """Test getting multiple users"""
    # Create multiple users
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            hashed_password=f"password{i}"
        )
        db_session.add(user)
        users.append(user)
    db_session.commit()
    
    # Get all users
    retrieved_users = user_repository.get_multi(db_session)
    
    # Check that all users were retrieved
    assert len(retrieved_users) >= len(users)
    
    # Get users with skip and limit
    retrieved_users = user_repository.get_multi(db_session, skip=1, limit=2)
    
    # Check that the correct users were retrieved
    assert len(retrieved_users) == 2


def test_get_active_users(db_session):
    """Test getting only active users"""
    # Create active and inactive users
    active_user = User(
        username="active",
        email="active@example.com",
        hashed_password="password",
        is_active=True
    )
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password="password",
        is_active=False
    )
    db_session.add(active_user)
    db_session.add(inactive_user)
    db_session.commit()
    
    # Get active users
    active_users = user_repository.get_active_users(db_session)
    
    # Check that only active users were retrieved
    assert any(user.username == "active" for user in active_users)
    assert not any(user.username == "inactive" for user in active_users)


def test_get_superusers(db_session):
    """Test getting only superusers"""
    # Create superuser and regular user
    superuser = User(
        username="admin",
        email="admin@example.com",
        hashed_password="password",
        is_superuser=True
    )
    regular_user = User(
        username="regular",
        email="regular@example.com",
        hashed_password="password",
        is_superuser=False
    )
    db_session.add(superuser)
    db_session.add(regular_user)
    db_session.commit()
    
    # Get superusers
    superusers = user_repository.get_superusers(db_session)
    
    # Check that only superusers were retrieved
    assert any(user.username == "admin" for user in superusers)
    assert not any(user.username == "regular" for user in superusers)


def test_increment_usage_count(db_session, test_user):
    """Test incrementing usage counts"""
    # Check initial counts
    assert test_user.sms_count == 0
    assert test_user.whatsapp_count == 0
    
    # Increment SMS count
    updated_user = user_repository.increment_usage_count(
        db_session, user_id=test_user.id, service_type="sms"
    )
    
    # Check that count was incremented
    assert updated_user.sms_count == 1
    assert updated_user.whatsapp_count == 0
    
    # Increment WhatsApp count
    updated_user = user_repository.increment_usage_count(
        db_session, user_id=test_user.id, service_type="whatsapp"
    )
    
    # Check that count was incremented
    assert updated_user.sms_count == 1
    assert updated_user.whatsapp_count == 1
    
    # Increment with invalid service type (should not change counts)
    updated_user = user_repository.increment_usage_count(
        db_session, user_id=test_user.id, service_type="invalid"
    )
    
    # Check that counts remained the same
    assert updated_user.sms_count == 1
    assert updated_user.whatsapp_count == 1
    
    # Increment with non-existent user ID
    updated_user = user_repository.increment_usage_count(
        db_session, user_id=999, service_type="sms"
    )
    
    # Check that None was returned
    assert updated_user is None 