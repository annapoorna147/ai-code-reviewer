from fastapi import FastAPI
from app.models.review import ReviewRequest, ReviewResponse
from app.services.code_analyzer import analyze_code

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
    findings = analyze_code(request.code)

    return ReviewResponse(
        language=request.language,
        total_issues=len(findings),
        findings=findings,
        status="issues_found" if findings else "clean"
    )
