import pytest
from pydantic import ValidationError

from app.models.auth import RegisterRequest, LoginRequest
from app.models.project import ProjectCreate, ProjectUpdate
from app.models.review import ReviewRequest, FixRequest, CodeMetrics


def test_registration_trims_username():
    request = RegisterRequest(
        username="  reviewer01  ",
        email="reviewer@example.com",
        password="SecurePass123",
    )
    assert request.username == "reviewer01"


@pytest.mark.parametrize("username", ["", "   ", "  \t  "])
def test_registration_rejects_blank_username(username):
    with pytest.raises(ValidationError):
        RegisterRequest(
            username=username,
            email="reviewer@example.com",
            password="SecurePass123",
        )


def test_login_preserves_password_exactly():
    request = LoginRequest(
        email="reviewer@example.com",
        password="  SecurePass123  ",
    )
    assert request.password == "  SecurePass123  "


def test_project_create_trims_name():
    project = ProjectCreate(name="  Review Tool  ")
    assert project.name == "Review Tool"


def test_project_update_trims_name():
    project = ProjectUpdate(name="  Updated Project  ")
    assert project.name == "Updated Project"


@pytest.mark.parametrize("name", ["", "   ", "  \t  "])
def test_project_create_rejects_blank_name(name):
    with pytest.raises(ValidationError):
        ProjectCreate(name=name)


@pytest.mark.parametrize("name", ["", "   ", "  \t  "])
def test_project_update_rejects_blank_name(name):
    with pytest.raises(ValidationError):
        ProjectUpdate(name=name)


def test_review_and_fix_code_size_limits():
    with pytest.raises(ValidationError):
        ReviewRequest(code="x" * 50001)

    with pytest.raises(ValidationError):
        FixRequest(
            code="x" * 50001,
            title="Finding",
            explanation="Explanation",
            suggestion="Suggestion",
        )


def test_code_metrics_lists_are_independent():
    first = CodeMetrics(
        lines_of_code=1,
        technical_debt={"estimated_minutes": 0, "estimated_hours": 0},
        analysis_status="success",
    )
    second = CodeMetrics(
        lines_of_code=1,
        technical_debt={"estimated_minutes": 0, "estimated_hours": 0},
        analysis_status="success",
    )

    first.function_complexities.append(
        {"name": "example", "line": 1, "complexity": 1}
    )

    assert second.function_complexities == []
