from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    user_id: int
    created_at: str
    updated_at: str
