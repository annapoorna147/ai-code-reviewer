import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.user_database import (
    initialize_user_database,
    get_user_by_email,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    import app.services.review_history as history

    monkeypatch.setattr(
        history,
        "DATABASE_PATH",
        tmp_path / "test_auth.db",
    )
    history.initialize_database()
    initialize_user_database()


def test_successful_registration():
    response = client.post(
        "/auth/register",
        json={
            "username": "authuser01",
            "email": "authuser01@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["username"] == "authuser01"


def test_duplicate_registration_is_rejected():
    payload = {
        "username": "authuser02",
        "email": "authuser02@example.com",
        "password": "SecurePass123",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_successful_login_returns_access_token():
    client.post(
        "/auth/register",
        json={
            "username": "authuser03",
            "email": "authuser03@example.com",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "authuser03@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_incorrect_password():
    client.post(
        "/auth/register",
        json={
            "username": "authuser04",
            "email": "authuser04@example.com",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "authuser04@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email():
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 401


def test_password_is_stored_as_hash():
    client.post(
        "/auth/register",
        json={
            "username": "authuser05",
            "email": "authuser05@example.com",
            "password": "SecurePass123",
        },
    )

    user = get_user_by_email("authuser05@example.com")

    assert user is not None
    assert user["password_hash"] != "SecurePass123"
