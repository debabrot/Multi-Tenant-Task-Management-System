"""Routers for User"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status

from app.backend.dependencies import get_current_user_id, get_user_service
from app.backend.services.user_service import UserService
from app.backend.schemas.user import (
    UserOut
)

# Initialize logger
logger = logging.getLogger(__name__)

# Define the API router
router = APIRouter(prefix="/user", tags=["user"])

@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    dependencies=[Depends(get_current_user_id)]
)
async def get_current_user_profile(
    current_user_id: UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> UserOut:
    """
    Get the current user's profile information.
    
    This endpoint requires a valid JWT access token in the Authorization header.
    The token is used to identify the current user and return their profile.
    
    Parameters
    ----------
    current_user_id : uuid.UUID
        The current user's ID extracted from the JWT token
    user_service : UserService
        Service for user operations
        
    Returns
    -------
    UserOut
        The current user's profile information
        
    Raises
    ------
    HTTPException
        401: If the token is invalid or expired
        403: If the user account is inactive
        404: If the user is not found
    """
    try:
        user_profile = await user_service.get_user_profile(current_user_id)
        logger.info(f"Retrieved profile for user {current_user_id}")
        return user_profile

    except HTTPException as e:
        logger.error(f"Failed to get user profile for {current_user_id}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error getting user profile for {current_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )