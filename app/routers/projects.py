from fastapi import APIRouter, Depends, HTTPException, status

from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.auth_dependency import get_current_user
from app.services.project_database import (
    create_project,
    get_projects,
    get_project,
    update_project,
    delete_project,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
):
    return create_project(
        name=project.name,
        description=project.description,
        user_id=current_user["id"],
    )


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    current_user: dict = Depends(get_current_user),
):
    return get_projects(user_id=current_user["id"])


@router.get("/{project_id}", response_model=ProjectResponse)
def retrieve_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    project = get_project(project_id, current_user["id"])

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def edit_project(
    project_id: int,
    project: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    updated = update_project(
        project_id=project_id,
        user_id=current_user["id"],
        name=project.name,
        description=project.description,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return updated


@router.delete("/{project_id}")
def remove_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    deleted = delete_project(project_id, current_user["id"])

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return {"message": "Project deleted successfully."}
