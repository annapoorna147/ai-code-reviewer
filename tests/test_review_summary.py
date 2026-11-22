from app.models.review import ReviewFinding
from app.services.review_summary import generate_review_summary


def make_finding(title, severity, line, priority, suggestion):
    return ReviewFinding(
        title=title,
        severity=severity,
        line=line,
        explanation="Test explanation.",
        suggestion=suggestion,
        priority_score=priority,
    )


def test_clean_code_generates_positive_summary():
    summary = generate_review_summary([], 100, 100)

    assert "No issues were detected" in summary.overall_assessment
    assert summary.key_risks == []
    assert summary.recommended_actions == []
    assert summary.fixing_order == []


def test_critical_findings_appear_first():
    findings = [
        make_finding("Minor issue", "low", 10, 20, "Improve this."),
        make_finding("Critical issue", "critical", 2, 100, "Fix immediately."),
    ]

    summary = generate_review_summary(findings, 60, 70)

    assert summary.key_risks[0].startswith("Critical issue")
    assert summary.fixing_order[0].startswith("Critical issue")


def test_summary_contains_recommendations():
    findings = [
        make_finding("Division issue", "high", 5, 80, "Validate the denominator."),
        make_finding("Input issue", "medium", 8, 60, "Validate user input."),
    ]

    summary = generate_review_summary(findings, 70, 90)

    assert "Validate the denominator." in summary.recommended_actions
    assert "Validate user input." in summary.recommended_actions


def test_ai_unavailability_is_disclosed():
    summary = generate_review_summary([], 100, 100, "unavailable")

    assert "AI analysis was unavailable" in summary.overall_assessment


def test_duplicate_recommendations_are_removed():
    findings = [
        make_finding("Issue one", "high", 1, 80, "Validate input."),
        make_finding("Issue two", "medium", 2, 60, "Validate input."),
    ]

    summary = generate_review_summary(findings, 70, 80)

    assert summary.recommended_actions == ["Validate input."]
