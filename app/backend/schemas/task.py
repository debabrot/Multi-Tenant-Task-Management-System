from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str | None = None
    due_at: datetime | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    due_at: datetime | None = None
    is_done: bool | None = None

class TaskOut(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    body: str | None
    due_at: datetime | None
    is_done: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskFilters(BaseModel):
    is_done: bool | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class TaskListOut(BaseModel):
    total: int
    items: list[TaskOut]