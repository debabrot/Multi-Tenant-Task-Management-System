"""
Task service for handling CRUD operations
"""

from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status

from app.backend.models.task import Task
from app.backend.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskFilters,
    TaskListOut,
    TaskOut
)


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    async def create_task(self, task_data: TaskCreate, owner_id: UUID) -> TaskOut:
        """
        Create a new task for the authenticated user.
        
        Parameters
        ----------
        task_data : TaskCreate
            Task creation data
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        TaskOut
            Created task data
        """
        db_task = Task(
            owner_id=owner_id,
            title=task_data.title,
            body=task_data.body,
            due_at=task_data.due_at
        )
        
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        
        return TaskOut.model_validate(db_task)

    async def get_task_by_id(self, task_id: UUID, owner_id: UUID) -> TaskOut:
        """
        Get a specific task by ID for the authenticated user.
        
        Parameters
        ----------
        task_id : UUID
            ID of the task to retrieve
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        TaskOut
            Task data
            
        Raises
        ------
        HTTPException
            If task is not found or doesn't belong to the user
        """
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskOut.model_validate(task)

    async def get_tasks(self, owner_id: UUID, filters: TaskFilters) -> TaskListOut:
        """
        Get paginated list of tasks for the authenticated user.
        
        Parameters
        ----------
        owner_id : UUID
            ID of the task owner
        filters : TaskFilters
            Filtering and pagination parameters
            
        Returns
        -------
        TaskListOut
            Paginated list of tasks
        """
        query = self.db.query(Task).filter(Task.owner_id == owner_id)
        
        # Apply filters
        if filters.is_done is not None:
            query = query.filter(Task.is_done == filters.is_done)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        tasks = query.order_by(Task.created_at.desc()).offset(filters.offset).limit(filters.limit).all()
        
        return TaskListOut(
            total=total,
            items=[TaskOut.model_validate(task) for task in tasks]
        )

    async def update_task(self, task_id: UUID, task_update: TaskUpdate, owner_id: UUID) -> TaskOut:
        """
        Update a specific task for the authenticated user.
        
        Parameters
        ----------
        task_id : UUID
            ID of the task to update
        task_update : TaskUpdate
            Task update data
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        TaskOut
            Updated task data
            
        Raises
        ------
        HTTPException
            If task is not found or doesn't belong to the user
        """
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update only provided fields
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        self.db.commit()
        self.db.refresh(task)
        
        return TaskOut.model_validate(task)

    async def delete_task(self, task_id: UUID, owner_id: UUID) -> None:
        """
        Delete a specific task for the authenticated user.
        
        Parameters
        ----------
        task_id : UUID
            ID of the task to delete
        owner_id : UUID
            ID of the task owner
            
        Raises
        ------
        HTTPException
            If task is not found or doesn't belong to the user
        """
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        self.db.delete(task)
        self.db.commit()

    async def mark_task_as_done(self, task_id: UUID, owner_id: UUID) -> TaskOut:
        """
        Mark a specific task as done for the authenticated user.
        
        Parameters
        ----------
        task_id : UUID
            ID of the task to mark as done
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        TaskOut
            Updated task data
            
        Raises
        ------
        HTTPException
            If task is not found or doesn't belong to the user
        """
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task.is_done = True
        self.db.commit()
        self.db.refresh(task)
        
        return TaskOut.model_validate(task)

    async def mark_task_as_undone(self, task_id: UUID, owner_id: UUID) -> TaskOut:
        """
        Mark a specific task as undone for the authenticated user.
        
        Parameters
        ----------
        task_id : UUID
            ID of the task to mark as undone
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        TaskOut
            Updated task data
            
        Raises
        ------
        HTTPException
            If task is not found or doesn't belong to the user
        """
        task = self.db.query(Task).filter(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task.is_done = False
        self.db.commit()
        self.db.refresh(task)
        
        return TaskOut.model_validate(task)

    async def get_task_stats(self, owner_id: UUID) -> dict:
        """
        Get task statistics for the authenticated user.
        
        Parameters
        ----------
        owner_id : UUID
            ID of the task owner
            
        Returns
        -------
        dict
            Task statistics including total, completed, and pending counts
        """
        total_tasks = self.db.query(func.count(Task.id)).filter(Task.owner_id == owner_id).scalar()
        completed_tasks = self.db.query(func.count(Task.id)).filter(
            and_(Task.owner_id == owner_id, Task.is_done == True)
        ).scalar()
        pending_tasks = total_tasks - completed_tasks
        
        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks
        }