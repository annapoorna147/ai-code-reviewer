from collections import Counter

from app.models.review import ReviewFinding, SeveritySummary


SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}


def calculate_quality_score(findings: list[ReviewFinding]) -> int:
    deductions = sum(
        SEVERITY_WEIGHTS[finding.severity]
        for finding in findings
    )

    return max(0, 100 - deductions)


def summarize_severity(
    findings: list[ReviewFinding]
) -> SeveritySummary:
    counts = Counter(finding.severity for finding in findings)

    return SeveritySummary(
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
    )
