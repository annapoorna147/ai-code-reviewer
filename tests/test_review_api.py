import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.review import ReviewFinding
from app.services.ai_reviewer import AIReviewError


client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_external_ai(monkeypatch):
    """Prevent automated tests from calling Gemini."""
    monkeypatch.setattr(
        "app.main.review_with_ai",
        lambda code: []
    )


def test_review_detects_eval():
    response = client.post(
        "/review",
        json={"code": "result = eval(user_input)"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] == 1
    assert data["quality_score"] == 85
    assert data["severity_summary"]["high"] == 1
    assert data["status"] == "issues_found"
    assert data["ai_status"] == "available"


def test_review_clean_code():
    response = client.post(
        "/review",
        json={"code": "print('Hello World')"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] == 0
    assert data["quality_score"] == 100
    assert data["status"] == "clean"
    assert data["ai_status"] == "available"


def test_review_syntax_error():
    response = client.post(
        "/review",
        json={"code": "def broken("}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] >= 1
    assert data["findings"][0]["title"] == "Python syntax error"
    assert data["quality_score"] == 85
    assert data["status"] == "issues_found"


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


def test_review_includes_ai_findings(monkeypatch):
    ai_finding = ReviewFinding(
        title="Possible division by zero",
        severity="high",
        line=2,
        explanation="The denominator may be zero.",
        suggestion="Check the denominator before division."
    )

    monkeypatch.setattr(
        "app.main.review_with_ai",
        lambda code: [ai_finding]
    )

    response = client.post(
        "/review",
        json={"code": "def calculate():\n    return 10 / value"}
    )

    assert response.status_code == 200
    data = response.json()

    assert any(
        finding["title"] == "Possible division by zero"
        for finding in data["findings"]
    )
    assert data["quality_score"] == 85
    assert data["severity_summary"]["high"] == 1
    assert data["ai_status"] == "available"


def test_review_works_when_ai_is_unavailable(monkeypatch):
    def unavailable_ai(code):
        raise AIReviewError("Gemini unavailable")

    monkeypatch.setattr(
        "app.main.review_with_ai",
        unavailable_ai
    )

    response = client.post(
        "/review",
        json={"code": "result = eval(user_input)"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] == 1
    assert data["quality_score"] == 85
    assert data["status"] == "issues_found"
    assert data["ai_status"] == "unavailable"


def test_clean_code_when_ai_is_unavailable(monkeypatch):
    def unavailable_ai(code):
        raise AIReviewError("Gemini unavailable")

    monkeypatch.setattr(
        "app.main.review_with_ai",
        unavailable_ai
    )

    response = client.post(
        "/review",
        json={"code": "print('Hello World')"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] == 0
    assert data["quality_score"] == 100
    assert data["status"] == "ai_unavailable"
    assert data["ai_status"] == "unavailable"
