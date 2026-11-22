from app.models.review import ReviewFinding, ReviewSummary


def generate_review_summary(
    findings: list[ReviewFinding],
    quality_score: int,
    security_score: int,
    ai_status: str = "available",
) -> ReviewSummary:
    if not findings:
        assessment = (
            "No issues were detected. The submitted code passed "
            "the available static and security checks."
        )

        if ai_status == "unavailable":
            assessment += " AI analysis was unavailable."

        return ReviewSummary(
            overall_assessment=assessment,
        )

    if quality_score < 50 or security_score < 50:
        assessment = (
            "The code requires significant attention. "
            "Address critical quality and security concerns first."
        )
    elif quality_score < 80 or security_score < 80:
        assessment = (
            "The code has improvement opportunities. "
            "Review the highest-priority findings before proceeding."
        )
    else:
        assessment = (
            "The code is in relatively good condition, "
            "but detected issues should be reviewed."
        )

    if ai_status == "unavailable":
        assessment += " AI analysis was unavailable."

    ranked_findings = sorted(
        findings,
        key=lambda finding: finding.priority_score or 0,
        reverse=True,
    )

    key_risks = [
        (
            f'{finding.title} '
            f'(Line {finding.line}, {finding.severity.upper()})'
        )
        for finding in ranked_findings[:3]
    ]

    recommended_actions = list(
        dict.fromkeys(
            finding.suggestion
            for finding in ranked_findings
        )
    )[:5]

    fixing_order = [
        (
            f'{finding.title} — Line {finding.line} '
            f'(Priority: {finding.priority_score or 0}/100)'
        )
        for finding in ranked_findings
    ]

    return ReviewSummary(
        overall_assessment=assessment,
        key_risks=key_risks,
        recommended_actions=recommended_actions,
        fixing_order=fixing_order,
    )
