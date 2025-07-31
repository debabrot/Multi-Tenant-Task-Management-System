# services/user_service.py
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

from app.backend.models.user import User
from app.backend.schemas.user import UserOut


class UserService:
    """Service for user-related operations"""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Parameters
        ----------
        user_id : uuid.UUID
            The user's unique identifier
            
        Returns
        -------
        Optional[User]
            The user if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_profile(self, user_id: uuid.UUID) -> UserOut:
        """
        Get user profile information by user ID.
        
        Parameters
        ----------
        user_id : uuid.UUID
            The user's unique identifier
            
        Returns
        -------
        UserOut
            User profile information
            
        Raises
        ------
        HTTPException
            If user is not found or inactive
        """
        user = await self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserOut.model_validate(user)
