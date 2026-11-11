from fastapi import FastAPI

from app.models.review import ReviewRequest, ReviewResponse
from app.services.code_analyzer import analyze_code
from app.services.ai_reviewer import review_with_ai, AIReviewError
from app.services.quality_scorer import (
    calculate_quality_score,
    summarize_severity,
)


app = FastAPI(
    title="AI Code Reviewer",
    description="An AI-powered code review platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Code Reviewer!",
        "status": "Running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/review", response_model=ReviewResponse)
def review_code(request: ReviewRequest):
    static_findings = analyze_code(request.code)

    ai_status = "available"

    try:
        ai_findings = review_with_ai(request.code)
    except AIReviewError:
        ai_findings = []
        ai_status = "unavailable"

    combined_findings = static_findings.copy()

    existing_findings = {
        (finding.title, finding.line)
        for finding in combined_findings
    }

    for finding in ai_findings:
        key = (finding.title, finding.line)

        if key not in existing_findings:
            combined_findings.append(finding)
            existing_findings.add(key)

    quality_score = calculate_quality_score(combined_findings)
    severity_summary = summarize_severity(combined_findings)

    if combined_findings:
        status = "issues_found"
    elif ai_status == "unavailable":
        status = "ai_unavailable"
    else:
        status = "clean"

    return ReviewResponse(
        language=request.language,
        quality_score=quality_score,
        total_issues=len(combined_findings),
        severity_summary=severity_summary,
        findings=combined_findings,
        status=status,
        ai_status=ai_status
    )
