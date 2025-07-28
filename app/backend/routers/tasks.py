"""
Task router for handling task-related endpoints
"""

from uuid import UUID
from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.backend.core.database import get_db
from app.backend.dependencies import get_current_user_id, get_task_service
from app.backend.services.task_service import TaskService
from app.backend.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskOut,
    TaskFilters,
    TaskListOut
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task for the authenticated user"
)
async def create_task(
    task_data: TaskCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskOut:
    """
    Create a new task for the authenticated user.
    """
    return await task_service.create_task(task_data, current_user_id)


@router.get(
    "/",
    response_model=TaskListOut,
    summary="Get all tasks",
    description="Get paginated list of tasks for the authenticated user with optional filtering"
)
async def get_tasks(
    is_done: bool | None = Query(None, description="Filter by completion status"),
    limit: int = Query(20, ge=1, le=100, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskListOut:
    """
    Get paginated list of tasks for the authenticated user.
    """
    filters = TaskFilters(is_done=is_done, limit=limit, offset=offset)
    return await task_service.get_tasks(current_user_id, filters)


@router.get(
    "/stats",
    response_model=Dict[str, int],
    summary="Get task statistics",
    description="Get task statistics for the authenticated user"
)
async def get_task_stats(
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, int]:
    """
    Get task statistics for the authenticated user.
    """
    return await task_service.get_task_stats(current_user_id)


@router.get(
    "/{task_id}",
    response_model=TaskOut,
    summary="Get a specific task",
    description="Get a specific task by ID for the authenticated user"
)
async def get_task(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskOut:
    """
    Get a specific task by ID for the authenticated user.
    """
    return await task_service.get_task_by_id(task_id, current_user_id)


@router.put(
    "/{task_id}",
    response_model=TaskOut,
    summary="Update a task",
    description="Update a specific task for the authenticated user"
)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskOut:
    """
    Update a specific task for the authenticated user.
    """
    return await task_service.update_task(task_id, task_update, current_user_id)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete a specific task for the authenticated user"
)
async def delete_task(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> None:
    """
    Delete a specific task for the authenticated user.
    """
    await task_service.delete_task(task_id, current_user_id)


@router.patch(
    "/{task_id}/done",
    response_model=TaskOut,
    summary="Mark task as done",
    description="Mark a specific task as completed for the authenticated user"
)
async def mark_task_as_done(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskOut:
    """
    Mark a specific task as done for the authenticated user.
    """
    return await task_service.mark_task_as_done(task_id, current_user_id)


@router.patch(
    "/{task_id}/undone",
    response_model=TaskOut,
    summary="Mark task as undone",
    description="Mark a specific task as not completed for the authenticated user"
)
async def mark_task_as_undone(
    task_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service)
) -> TaskOut:
    """
    Mark a specific task as undone for the authenticated user.
    """
    return await task_service.mark_task_as_undone(task_id, current_user_id)