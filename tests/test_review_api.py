import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_dependency import get_current_user
from app.models.review import ReviewFinding
from app.services.ai_reviewer import AIReviewError


client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_external_ai(monkeypatch):
    """Prevent Gemini calls and authenticate review test requests."""
    monkeypatch.setattr(
        "app.main.review_with_ai",
        lambda code: []
    )

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 999,
        "username": "review_test_user",
        "email": "review-test@example.com",
    }

    yield

    app.dependency_overrides.pop(get_current_user, None)


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


def test_review_returns_advanced_metrics():
    code = """
def calculate(a, b):
    if a > b:
        return a
    return b
"""
    response = client.post("/review", json={"code": code})

    assert response.status_code == 200
    metrics = response.json()["code_metrics"]

    assert metrics["analysis_status"] == "success"
    assert metrics["lines_of_code"] > 0
    assert metrics["total_complexity"] >= 1
    assert 0 <= metrics["maintainability_index"] <= 100
    assert "technical_debt" in metrics
    assert "duplicate_blocks" in metrics


def test_review_metrics_for_syntax_error():
    response = client.post(
        "/review",
        json={"code": "def broken("}
    )

    assert response.status_code == 200
    metrics = response.json()["code_metrics"]

    assert metrics["analysis_status"] == "syntax_error"
    assert metrics["total_complexity"] is None
    assert metrics["maintainability_index"] is None


def test_review_metrics_when_ai_unavailable(monkeypatch):
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

    assert data["ai_status"] == "unavailable"
    assert data["code_metrics"]["analysis_status"] == "success"


def test_review_response_model_supports_missing_metrics():
    from app.models.review import ReviewResponse, SeveritySummary

    result = ReviewResponse(
        language="python",
        quality_score=100,
        total_issues=0,
        severity_summary=SeveritySummary(),
        findings=[],
        status="clean",
        ai_status="available",
    )

    assert result.code_metrics is None


def test_fix_endpoint_returns_proposed_code(monkeypatch):
    original_code = "result = eval(user_input)"
    fixed_code = "result = ast.literal_eval(user_input)"

    monkeypatch.setattr(
        "app.main.generate_fix",
        lambda **kwargs: fixed_code,
    )

    response = client.post(
        "/fix",
        json={
            "code": original_code,
            "title": "Unsafe eval",
            "explanation": "eval can execute arbitrary code.",
            "suggestion": "Use a safer parsing method.",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["original_code"] == original_code
    assert data["fixed_code"] == fixed_code
    assert data["status"] == "success"


def test_fix_endpoint_handles_ai_unavailability(monkeypatch):
    def unavailable_fix(**kwargs):
        from app.services.fix_generator import FixGenerationError
        raise FixGenerationError("Gemini is unavailable.")

    monkeypatch.setattr(
        "app.main.generate_fix",
        unavailable_fix,
    )

    response = client.post(
        "/fix",
        json={
            "code": "print('hello')",
            "title": "Example issue",
            "explanation": "Example explanation.",
            "suggestion": "Example suggestion.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Gemini is unavailable."


def test_review_returns_findings_in_priority_order(monkeypatch):
    findings = [
        ReviewFinding(
            title="Minor issue",
            severity="low",
            line=1,
            explanation="Minor concern.",
            suggestion="Consider improving this.",
            confidence="low",
        ),
        ReviewFinding(
            title="Critical issue",
            severity="critical",
            line=2,
            explanation="Serious concern.",
            suggestion="Fix immediately.",
            confidence="high",
        ),
    ]

    monkeypatch.setattr(
        "app.main.review_with_ai",
        lambda code: findings,
    )

    response = client.post(
        "/review",
        json={"code": "print('hello')\nprint('world')"},
    )

    assert response.status_code == 200

    returned_findings = response.json()["findings"]

    assert returned_findings[0]["title"] == "Critical issue"
    assert returned_findings[0]["priority_score"] == 100
    assert returned_findings[1]["title"] == "Minor issue"
    assert returned_findings[1]["priority_score"] == 20
