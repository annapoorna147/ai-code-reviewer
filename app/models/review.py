from typing import Literal

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Source code to review"
    )

    language: Literal["python"] = Field(
        default="python",
        description="Programming language"
    )


class ReviewFinding(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    line: int
    explanation: str
    suggestion: str


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ReviewResponse(BaseModel):
    language: str
    quality_score: int = Field(ge=0, le=100)
    total_issues: int
    severity_summary: SeveritySummary
    findings: list[ReviewFinding]
    status: Literal["clean", "issues_found", "ai_unavailable"]
    ai_status: Literal["available", "unavailable"]
