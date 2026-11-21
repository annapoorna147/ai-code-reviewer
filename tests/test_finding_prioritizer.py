from app.models.review import ReviewFinding
from app.services.finding_prioritizer import prioritize_findings


def make_finding(title, severity, confidence=None):
    return ReviewFinding(
        title=title,
        severity=severity,
        line=1,
        explanation="Test explanation",
        suggestion="Test suggestion",
        confidence=confidence,
    )


def test_critical_findings_are_prioritized_first():
    findings = [
        make_finding("Minor issue", "low"),
        make_finding("Critical issue", "critical"),
        make_finding("High issue", "high"),
    ]

    prioritized = prioritize_findings(findings)

    assert prioritized[0].title == "Critical issue"
    assert prioritized[1].title == "High issue"
    assert prioritized[2].title == "Minor issue"


def test_high_confidence_increases_priority():
    findings = [
        make_finding("Uncertain issue", "high", "low"),
        make_finding("Confirmed issue", "high", "high"),
    ]

    prioritized = prioritize_findings(findings)

    assert prioritized[0].title == "Confirmed issue"


def test_priority_scores_are_between_zero_and_one_hundred():
    findings = [
        make_finding("Critical issue", "critical", "high"),
        make_finding("Minor issue", "low", "low"),
    ]

    prioritized = prioritize_findings(findings)

    for finding in prioritized:
        assert 0 <= finding.priority_score <= 100


def test_original_findings_are_not_modified():
    finding = make_finding("Example issue", "medium")

    prioritized = prioritize_findings([finding])

    assert finding.priority_score is None
    assert prioritized[0].priority_score is not None
