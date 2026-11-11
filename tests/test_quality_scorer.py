from app.models.review import ReviewFinding
from app.services.quality_scorer import (
    calculate_quality_score,
    summarize_severity,
)


def make_finding(severity):
    return ReviewFinding(
        title="Test finding",
        severity=severity,
        line=1,
        explanation="Test explanation",
        suggestion="Test suggestion",
    )


def test_clean_code_gets_100_score():
    assert calculate_quality_score([]) == 100


def test_severity_deductions():
    findings = [
        make_finding("critical"),
        make_finding("high"),
        make_finding("medium"),
        make_finding("low"),
    ]

    assert calculate_quality_score(findings) == 49


def test_score_never_goes_below_zero():
    findings = [make_finding("critical") for _ in range(5)]

    assert calculate_quality_score(findings) == 0


def test_severity_summary():
    findings = [
        make_finding("critical"),
        make_finding("high"),
        make_finding("high"),
        make_finding("medium"),
        make_finding("low"),
        make_finding("low"),
    ]

    summary = summarize_severity(findings)

    assert summary.critical == 1
    assert summary.high == 2
    assert summary.medium == 1
    assert summary.low == 2


def test_empty_findings_have_zero_severity_counts():
    summary = summarize_severity([])

    assert summary.critical == 0
    assert summary.high == 0
    assert summary.medium == 0
    assert summary.low == 0
