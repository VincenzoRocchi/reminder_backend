import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_create_user(client, superuser_token_headers):
    data = {
        "email": "new@example.com",
        "full_name": "New User",
        "password": "newpassword",
        "phone_number": "1234567890"
    }
    response = client.post(
        "/api/v1/users/",
        json=data,
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    new_user = response.json()
    assert new_user["email"] == data["email"]
    assert new_user["full_name"] == data["full_name"]
    assert new_user["phone_number"] == data["phone_number"]
    assert "password" not in new_user
    assert "hashed_password" not in new_user


def test_read_users(client, superuser_token_headers, test_user):
    response = client.get(
        "/api/v1/users/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 1  # At least the test user should be present
    assert any(user["email"] == test_user.email for user in users)


def test_read_user(client, token_headers, test_user):
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=token_headers,
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user.email
    assert user_data["full_name"] == test_user.full_name


def test_update_user(client, token_headers, test_user):
    data = {
        "full_name": "Updated Name",
    }
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json=data,
        headers=token_headers,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == data["full_name"]
    assert updated_user["email"] == test_user.email  # Unchanged


def test_register_user(client):
    data = {
        "email": "register@example.com",
        "full_name": "Registered User",
        "password": "password",
        "phone_number": "9876543210"
    }
    response = client.post(
        "/api/v1/users/register",
        json=data,
    )
    assert response.status_code == 200
    new_user = response.json()
    assert new_user["email"] == data["email"]
    assert new_user["full_name"] == data["full_name"]
    assert new_user["phone_number"] == data["phone_number"]