from types import SimpleNamespace

import pytest

from app.services import ai_reviewer
from app.services.ai_reviewer import AIReviewError, review_with_ai


def mock_gemini(monkeypatch, findings):
    response = SimpleNamespace(
        text=__import__("json").dumps({"findings": findings})
    )

    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: response
        )
    )

    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setattr(
        ai_reviewer.genai,
        "Client",
        lambda **kwargs: fake_client,
    )


def test_ai_returns_advanced_intelligence_fields(monkeypatch):
    mock_gemini(monkeypatch, [{
        "title": "Inefficient loop",
        "severity": "medium",
        "line": 2,
        "explanation": "Repeated work is performed.",
        "suggestion": "Use a set for faster lookups.",
        "root_cause": "List membership is checked repeatedly.",
        "impact": "Execution time increases for large inputs.",
        "confidence": "high",
    }])

    findings = review_with_ai("items = []\nfor x in values:\n    if x in items:\n        pass")

    assert len(findings) == 1
    assert findings[0].root_cause == "List membership is checked repeatedly."
    assert findings[0].impact == "Execution time increases for large inputs."
    assert findings[0].confidence == "high"


def test_ai_accepts_legacy_findings_without_new_fields(monkeypatch):
    mock_gemini(monkeypatch, [{
        "title": "Example issue",
        "severity": "low",
        "line": 1,
        "explanation": "Example explanation.",
        "suggestion": "Example suggestion.",
    }])

    findings = review_with_ai("print('hello')")

    assert len(findings) == 1
    assert findings[0].root_cause is None
    assert findings[0].impact is None
    assert findings[0].confidence is None


def test_ai_rejects_invalid_confidence(monkeypatch):
    mock_gemini(monkeypatch, [{
        "title": "Example issue",
        "severity": "low",
        "line": 1,
        "explanation": "Example explanation.",
        "suggestion": "Example suggestion.",
        "confidence": "very_high",
    }])

    with pytest.raises(AIReviewError):
        review_with_ai("print('hello')")


def test_ai_filters_invalid_line_numbers(monkeypatch):
    mock_gemini(monkeypatch, [{
        "title": "Invalid line issue",
        "severity": "low",
        "line": 10,
        "explanation": "Example explanation.",
        "suggestion": "Example suggestion.",
    }])

    findings = review_with_ai("print('hello')")

    assert findings == []


def test_ai_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(AIReviewError, match="API key"):
        review_with_ai("print('hello')")
