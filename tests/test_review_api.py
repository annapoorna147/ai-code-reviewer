from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_review_detects_eval():
    response = client.post(
        "/review",
        json={"code": "result = eval(user_input)"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_issues"] >= 1
    assert data["status"] == "issues_found"


def test_review_clean_code():
    response = client.post(
        "/review",
        json={"code": "print('Hello World')"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_issues"] == 0
    assert data["status"] == "clean"


def test_review_syntax_error():
    response = client.post(
        "/review",
        json={"code": "def broken("}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_issues"] >= 1
    assert data["findings"][0]["title"] == "Python syntax error"


def test_review_empty_code():
    response = client.post(
        "/review",
        json={"code": ""}
    )

    assert response.status_code == 422


def test_review_unsupported_language():
    response = client.post(
        "/review",
        json={
            "code": "print('Hello')",
            "language": "javascript"
        }
    )

    assert response.status_code == 422
