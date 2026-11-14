from fastapi import FastAPI, HTTPException, Depends
from app.services.auth_dependency import get_current_user
from app.routers.auth import router as auth_router
from app.services.user_database import initialize_user_database

from app.models.review import ReviewRequest, ReviewResponse
from app.services.code_analyzer import analyze_code
from app.services.ai_reviewer import review_with_ai, AIReviewError
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


app.include_router(auth_router)


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

    result = ReviewResponse(
        language=request.language,
        quality_score=quality_score,
        total_issues=len(combined_findings),
        severity_summary=severity_summary,
        findings=combined_findings,
        status=status,
        ai_status=ai_status
    )

    save_review(request.code, result, user_id=current_user['id'])

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
