import pytest
from unittest.mock import patch, MagicMock
import uuid
from sqlalchemy.exc import IntegrityError

from app.models.users import User
from app.core.exceptions import SensitiveDataStorageError


def test_user_model_creation():
    """Test that a User model can be created with basic attributes"""
    # Create a user with minimal attributes
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Check basic attributes
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_value"
    assert user.is_active is True  # Default value
    assert user.is_superuser is False  # Default value
    
    # Check that created_at is None before database insertion
    assert user.created_at is None
    
    # Check string representation
    assert str(user) == "User: testuser (test@example.com)"
    assert "id=None" in repr(user)
    assert "username='testuser'" in repr(user)


def test_user_model_with_optional_attributes():
    """Test that a User model can be created with optional attributes"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value",
        first_name="Test",
        last_name="User",
        business_name="Test Business",
        is_active=False,
        is_superuser=True
    )
    
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.business_name == "Test Business"
    assert user.is_active is False
    assert user.is_superuser is True


@patch('app.core.encryption.encryption_service.encrypt_string')
def test_phone_number_setter(mock_encrypt):
    """Test that phone_number property setter encrypts the value"""
    # Configure mock
    mock_encrypt.return_value = "encrypted_phone_number"
    
    # Create user and set phone number
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    user.phone_number = "1234567890"
    
    # Check that encryption was called
    mock_encrypt.assert_called_once_with("1234567890")
    
    # Check that encrypted value was stored
    assert user._phone_number == "encrypted_phone_number"


@patch('app.core.encryption.encryption_service.decrypt_string')
def test_phone_number_getter(mock_decrypt):
    """Test that phone_number property getter decrypts the value"""
    # Configure mock
    mock_decrypt.return_value = "1234567890"
    
    # Create user with encrypted phone number
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value",
        _phone_number="encrypted_phone_number"
    )
    
    # Check that decryption returns the correct value
    assert user.phone_number == "1234567890"
    
    # Check that decryption was called
    mock_decrypt.assert_called_once_with("encrypted_phone_number")


@patch('app.core.encryption.encryption_service.decrypt_string')
def test_phone_number_getter_handles_none(mock_decrypt):
    """Test that phone_number property getter handles None value"""
    # Create user with no phone number
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value",
        _phone_number=None
    )
    
    # Check that None is returned directly
    assert user.phone_number is None
    
    # Check that decryption was not called
    mock_decrypt.assert_not_called()


@patch('app.core.encryption.encryption_service.decrypt_string')
def test_phone_number_getter_handles_error(mock_decrypt):
    """Test that phone_number property getter handles decryption errors"""
    # Configure mock to raise an exception
    mock_decrypt.side_effect = Exception("Decryption failed")
    
    # Create user with encrypted phone number
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value",
        _phone_number="encrypted_phone_number"
    )
    
    # Check that None is returned on error
    assert user.phone_number is None
    
    # Check that decryption was called but failed
    mock_decrypt.assert_called_once_with("encrypted_phone_number")


@patch('app.core.encryption.encryption_service.encrypt_string')
def test_phone_number_setter_handles_none(mock_encrypt):
    """Test that phone_number property setter handles None value"""
    # Create user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Set phone number to None
    user.phone_number = None
    
    # Check that _phone_number is None
    assert user._phone_number is None
    
    # Check that encryption was not called
    mock_encrypt.assert_not_called()


@patch('app.core.encryption.encryption_service.encrypt_string')
def test_phone_number_setter_handles_error(mock_encrypt):
    """Test that phone_number property setter handles encryption errors"""
    # Configure mock to raise an exception
    mock_encrypt.side_effect = Exception("Encryption failed")
    
    # Create user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Check that exception is raised
    with pytest.raises(SensitiveDataStorageError) as excinfo:
        user.phone_number = "1234567890"
    
    # Check exception message
    assert "phone number" in str(excinfo.value)
    
    # Check that encryption was called but failed
    mock_encrypt.assert_called_once_with("1234567890")


def test_user_model_persistence(db_session):
    """Test that a User model can be persisted to the database"""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Add to session and commit
    db_session.add(user)
    db_session.commit()
    
    # Check that ID was assigned
    assert user.id is not None
    
    # Check that created_at was set
    assert user.created_at is not None
    
    # Check that user can be retrieved
    retrieved_user = db_session.query(User).filter_by(id=user.id).first()
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"


def test_user_model_constraints(db_session):
    """Test that User model constraints are enforced"""
    # Create a user
    user1 = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Add to session and commit
    db_session.add(user1)
    db_session.commit()
    
    # Try to create another user with the same username
    user2 = User(
        username="testuser",  # Same username
        email="different@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Add to session and check that commit raises an exception
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback for next test
    db_session.rollback()
    
    # Try to create another user with the same email
    user3 = User(
        username="differentuser",
        email="test@example.com",  # Same email
        hashed_password="hashed_password_value"
    )
    
    # Add to session and check that commit raises an exception
    db_session.add(user3)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_model_required_fields(db_session):
    """Test that User model required fields are enforced"""
    # Try to create a user without username
    user_no_username = User(
        email="test@example.com",
        hashed_password="hashed_password_value"
    )
    
    # Add to session and check that commit raises an exception
    db_session.add(user_no_username)
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback for next test
    db_session.rollback()
    
    # Try to create a user without email
    user_no_email = User(
        username="testuser",
        hashed_password="hashed_password_value"
    )
    
    # Add to session and check that commit raises an exception
    db_session.add(user_no_email)
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback for next test
    db_session.rollback()
    
    # Try to create a user without hashed_password
    user_no_password = User(
        username="testuser",
        email="test@example.com"
    )
    
    # Add to session and check that commit raises an exception
    db_session.add(user_no_password)
    with pytest.raises(IntegrityError):
        db_session.commit() 