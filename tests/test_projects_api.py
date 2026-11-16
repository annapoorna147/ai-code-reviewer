import pytest
from fastapi.testclient import TestClient

import app.services.review_history as history
from app.main import app
from app.services.auth_dependency import get_current_user
from app.services.project_database import initialize_project_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "DATABASE_PATH", tmp_path / "test_projects.db")
    history.initialize_database()
    initialize_project_database()


@pytest.fixture(autouse=True)
def authenticate_user():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 999,
        "username": "project_test_user",
        "email": "project-test@example.com",
    }
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_create_project():
    response = client.post("/projects/", json={
        "name": "AI Code Reviewer",
        "description": "An intelligent code review platform.",
    })
    assert response.status_code == 201
    assert response.json()["name"] == "AI Code Reviewer"
    assert response.json()["user_id"] == 999


def test_list_projects():
    client.post("/projects/", json={"name": "Project One"})
    client.post("/projects/", json={"name": "Project Two"})

    response = client.get("/projects/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Project Two"


def test_get_project_details():
    created = client.post("/projects/", json={"name": "AI Code Reviewer"})
    project_id = created.json()["id"]

    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_update_project():
    created = client.post("/projects/", json={"name": "Old Project"})
    project_id = created.json()["id"]

    response = client.put(f"/projects/{project_id}", json={
        "name": "Updated Project",
        "description": "Updated description",
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"


def test_delete_project():
    created = client.post("/projects/", json={"name": "Temporary Project"})
    project_id = created.json()["id"]

    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200
    assert client.get(f"/projects/{project_id}").status_code == 404


def test_user_cannot_access_another_users_project():
    created = client.post("/projects/", json={"name": "Private Project"})
    project_id = created.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1000,
        "username": "another_user",
        "email": "another@example.com",
    }

    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 404


def test_user_only_sees_their_own_projects():
    client.post("/projects/", json={"name": "User One Project"})

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1000,
        "username": "another_user",
        "email": "another@example.com",
    }

    response = client.get("/projects/")
    assert response.status_code == 200
    assert response.json() == []


def test_missing_project_returns_404():
    response = client.get("/projects/999")
    assert response.status_code == 404


def test_invalid_project_name_is_rejected():
    response = client.post("/projects/", json={"name": "AB"})
    assert response.status_code == 422

def test_review_can_be_linked_to_project(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "review_with_ai", lambda code: [])

    created = client.post("/projects/", json={"name": "Review Project"})
    project_id = created.json()["id"]

    response = client.post("/review", json={
        "code": "x = 1",
        "project_id": project_id,
    })

    assert response.status_code == 200

    history_response = client.get(
        f"/projects/{project_id}/history"
    )

    assert history_response.status_code == 200
    data = history_response.json()
    assert data["project_id"] == project_id
    assert data["total"] == 1
    assert len(data["reviews"]) == 1


def test_project_history_only_contains_linked_reviews(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "review_with_ai", lambda code: [])

    created = client.post("/projects/", json={"name": "History Project"})
    project_id = created.json()["id"]

    client.post("/review", json={
        "code": "x = 1",
        "project_id": project_id,
    })

    client.post("/review", json={"code": "y = 2"})

    response = client.get(f"/projects/{project_id}/history")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_user_cannot_link_review_to_another_users_project(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "review_with_ai", lambda code: [])

    created = client.post("/projects/", json={"name": "Private Project"})
    project_id = created.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1000,
        "username": "another_user",
        "email": "another@example.com",
    }

    response = client.post("/review", json={
        "code": "x = 1",
        "project_id": project_id,
    })

    assert response.status_code == 404

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 999,
        "username": "project_test_user",
        "email": "project-test@example.com",
    }

    history_response = client.get(
        f"/projects/{project_id}/history"
    )

    assert history_response.status_code == 200
    assert history_response.json()["total"] == 0


def test_standalone_review_still_works(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "review_with_ai", lambda code: [])

    response = client.post("/review", json={
        "code": "x = 1",
    })

    assert response.status_code == 200

