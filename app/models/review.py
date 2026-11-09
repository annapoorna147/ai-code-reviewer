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


class ReviewResponse(BaseModel):
    language: str
    total_issues: int
    findings: list[ReviewFinding]
    status: str
