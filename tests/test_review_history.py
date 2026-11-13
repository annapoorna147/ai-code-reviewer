import app.services.review_history as history

from app.models.review import (
    ReviewResponse,
    SeveritySummary,
)


def sample_result():
    return ReviewResponse(
        language="python",
        quality_score=85,
        total_issues=1,
        severity_summary=SeveritySummary(
            critical=0,
            high=1,
            medium=0,
            low=0,
        ),
        findings=[],
        status="issues_found",
        ai_status="unavailable",
    )


def setup_test_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        history,
        "DATABASE_PATH",
        tmp_path / "test_reviews.db",
    )
    history.initialize_database()


def test_save_and_retrieve_review(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    review_id = history.save_review(
        "print('Hello')",
        sample_result(),
    )

    saved = history.get_review(review_id)

    assert saved is not None
    assert saved["code"] == "print('Hello')"
    assert saved["result"]["quality_score"] == 85


def test_get_history(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    history.save_review("print(1)", sample_result())
    history.save_review("print(2)", sample_result())

    reviews = history.get_history()

    assert len(reviews) == 2
    assert reviews[0]["quality_score"] == 85
    assert reviews[0]["total_issues"] == 1


def test_missing_review_returns_none(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    assert history.get_review(999) is None


def test_history_limit(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    for number in range(3):
        history.save_review(
            f"print({number})",
            sample_result(),
        )

    reviews = history.get_history(limit=2)

    assert len(reviews) == 2
