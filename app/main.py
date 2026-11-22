from fastapi import FastAPI, HTTPException, Depends
from app.services.auth_dependency import get_current_user
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.services.user_database import initialize_user_database
from app.services.project_database import (
    initialize_project_database,
    get_project,
)

from app.models.review import ReviewRequest, ReviewResponse, FixRequest
from app.services.code_analyzer import analyze_code
from app.services.security_analyzer import analyze_security
from app.services.advanced_metrics import analyze_advanced_metrics
from app.services.ai_reviewer import review_with_ai, AIReviewError
from app.services.fix_generator import generate_fix, FixGenerationError
from app.services.finding_prioritizer import prioritize_findings
from app.services.review_summary import generate_review_summary
from app.services.quality_scorer import (
    calculate_quality_score,
    summarize_severity,
)
from app.services.review_history import (
    initialize_database,
    save_review,
    get_history,
    get_review,
    get_analytics,
)


app = FastAPI(
    title="AI Code Reviewer",
    description="An AI-powered code review platform",
    version="1.0.0"
)

initialize_database()
initialize_user_database()
initialize_project_database()


app.include_router(auth_router)
app.include_router(projects_router)


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
def review_code(request: ReviewRequest, current_user: dict = Depends(get_current_user)):
    if request.project_id is not None:
        project = get_project(request.project_id, current_user["id"])

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found."
            )

    static_findings = analyze_code(request.code)

    ai_status = "available"

    try:
        ai_findings = review_with_ai(request.code)
    except AIReviewError:
        ai_findings = []
        ai_status = "unavailable"

    combined_findings = static_findings.copy()

    # Add security vulnerability findings.
    security_findings = analyze_security(request.code)

    for finding in security_findings:
        if not any(
            existing.title == finding.title and existing.line == finding.line
            for existing in combined_findings
        ):
            combined_findings.append(finding)

    existing_findings = {
        (finding.title, finding.line)
        for finding in combined_findings
    }

    for finding in ai_findings:
        key = (finding.title, finding.line)

        if key not in existing_findings:
            combined_findings.append(finding)
            existing_findings.add(key)

    combined_findings = prioritize_findings(combined_findings)

    quality_score = calculate_quality_score(combined_findings)
    severity_summary = summarize_severity(combined_findings)
    code_metrics = analyze_advanced_metrics(request.code, combined_findings)

    # Calculate a separate security score.
    deductions = {
        "critical": 25,
        "high": 15,
        "medium": 8,
        "low": 3,
    }

    security_score = max(
        0,
        100 - sum(
            deductions[finding.severity]
            for finding in security_findings
        ),
    )

    review_summary = generate_review_summary(
        findings=combined_findings,
        quality_score=quality_score,
        security_score=security_score,
        ai_status=ai_status,
    )

    if combined_findings:
        status = "issues_found"
    elif ai_status == "unavailable":
        status = "ai_unavailable"
    else:
        status = "clean"

    result = ReviewResponse(
        language=request.language,
        quality_score=quality_score,
        total_issues=len(combined_findings),
        severity_summary=severity_summary,
        findings=combined_findings,
        status=status,
        ai_status=ai_status,
        code_metrics=code_metrics,
        security_score=security_score,
        review_summary=review_summary,
    )

    save_review(
        request.code,
        result,
        user_id=current_user["id"],
        project_id=request.project_id,
    )

    return result


@app.get("/history")
def review_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100."
        )

    reviews = get_history(limit, user_id=current_user["id"])

    return {
        "total": len(reviews),
        "reviews": reviews
    }


@app.get("/history/{review_id}")
def review_history_detail(review_id: int, current_user: dict = Depends(get_current_user)):
    review = get_review(review_id, user_id=current_user['id'])

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found."
        )

    return review


@app.get("/analytics")
def review_analytics(current_user: dict = Depends(get_current_user)):
    return get_analytics(user_id=current_user["id"])


@app.post("/fix")
def fix_code(
    request: FixRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        fixed_code = generate_fix(
            code=request.code,
            title=request.title,
            explanation=request.explanation,
            suggestion=request.suggestion,
        )

        return {
            "original_code": request.code,
            "fixed_code": fixed_code,
            "status": "success",
        }

    except FixGenerationError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from None


@app.post("/fix")
def fix_code(
    request: FixRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        fixed_code = generate_fix(
            code=request.code,
            title=request.title,
            explanation=request.explanation,
            suggestion=request.suggestion,
        )

        return {
            "original_code": request.code,
            "fixed_code": fixed_code,
            "status": "success",
        }

    except FixGenerationError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from None
