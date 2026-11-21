from app.models.review import ReviewFinding


SEVERITY_PRIORITY = {
    "critical": 100,
    "high": 80,
    "medium": 60,
    "low": 40,
}

CONFIDENCE_ADJUSTMENT = {
    "high": 0,
    "medium": -10,
    "low": -20,
    None: -10,
}


def prioritize_findings(
    findings: list[ReviewFinding],
) -> list[ReviewFinding]:
    prioritized = []

    for finding in findings:
        base_score = SEVERITY_PRIORITY[finding.severity]
        adjustment = CONFIDENCE_ADJUSTMENT[finding.confidence]

        priority_score = max(
            0,
            min(100, base_score + adjustment),
        )

        prioritized.append(
            finding.model_copy(
                update={"priority_score": priority_score}
            )
        )

    return sorted(
        prioritized,
        key=lambda finding: finding.priority_score,
        reverse=True,
    )
