import pytest
from fastapi.testclient import TestClient

import app.services.review_history as history
from app.main import app
from app.services.auth_dependency import get_current_user


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        history,
        "DATABASE_PATH",
        tmp_path / "test_reviews.db",
    )
    history.initialize_database()


@pytest.fixture(autouse=True)
def disable_external_ai(monkeypatch):
    monkeypatch.setattr(
        "app.main.review_with_ai",
        lambda code: [],
    )

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 999,
        "username": "history_test_user",
        "email": "history-test@example.com",
    }

    yield

    app.dependency_overrides.pop(get_current_user, None)


def test_review_is_saved_to_history():
    response = client.post(
        "/review",
        json={"code": "result = eval(user_input)"},
    )

    assert response.status_code == 200

    history_response = client.get("/history")

    assert history_response.status_code == 200

    data = history_response.json()
    assert data["total"] == 1
    assert data["reviews"][0]["quality_score"] == 85
    assert data["reviews"][0]["total_issues"] == 1


def test_get_review_history_detail():
    client.post(
        "/review",
        json={"code": "print('Hello')"},
    )

    history_response = client.get("/history")
    review_id = history_response.json()["reviews"][0]["id"]

    detail_response = client.get(f"/history/{review_id}")

    assert detail_response.status_code == 200

    data = detail_response.json()
    assert data["id"] == review_id
    assert data["code"] == "print('Hello')"
    assert data["result"]["quality_score"] == 100


def test_history_returns_newest_review_first():
    client.post(
        "/review",
        json={"code": "print('First')"},
    )
    client.post(
        "/review",
        json={"code": "print('Second')"},
    )

    response = client.get("/history")

    reviews = response.json()["reviews"]

    assert len(reviews) == 2
    assert reviews[0]["id"] > reviews[1]["id"]


def test_missing_review_returns_404():
    response = client.get("/history/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found."


def test_invalid_history_limit_returns_400():
    response = client.get("/history?limit=0")

    assert response.status_code == 400


def test_history_limit_over_100_returns_400():
    response = client.get("/history?limit=101")

    assert response.status_code == 400
