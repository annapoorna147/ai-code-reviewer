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

    project_id: int | None = Field(
        default=None,
        gt=0,
        description="Optional project ID associated with this review"
    )


class ReviewFinding(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    line: int
    explanation: str
    suggestion: str
    root_cause: str | None = None
    impact: str | None = None
    confidence: Literal["low", "medium", "high"] | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class FunctionComplexity(BaseModel):
    name: str
    line: int
    complexity: int = Field(ge=1)


class DuplicateBlock(BaseModel):
    lines: int
    occurrences: int
    code: list[str]


class TechnicalDebt(BaseModel):
    estimated_minutes: int = Field(ge=0)
    estimated_hours: float = Field(ge=0)


class CodeMetrics(BaseModel):
    lines_of_code: int = Field(ge=0)
    total_complexity: int | None = Field(default=None, ge=0)
    function_complexities: list[FunctionComplexity] = []
    maintainability_index: float | None = Field(default=None, ge=0, le=100)
    duplicate_blocks: list[DuplicateBlock] = []
    technical_debt: TechnicalDebt
    analysis_status: Literal["success", "syntax_error"]


class ReviewSummary(BaseModel):
    overall_assessment: str
    key_risks: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    fixing_order: list[str] = Field(default_factory=list)


class ReviewResponse(BaseModel):
    language: str
    quality_score: int = Field(ge=0, le=100)
    total_issues: int
    severity_summary: SeveritySummary
    findings: list[ReviewFinding]
    status: Literal["clean", "issues_found", "ai_unavailable"]
    ai_status: Literal["available", "unavailable"]
    code_metrics: CodeMetrics | None = None
    security_score: int = Field(default=100, ge=0, le=100)
    review_summary: ReviewSummary | None = None


class FixRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50000)
    title: str = Field(..., min_length=1, max_length=200)
    explanation: str = Field(..., min_length=1, max_length=2000)
    suggestion: str = Field(..., min_length=1, max_length=2000)
