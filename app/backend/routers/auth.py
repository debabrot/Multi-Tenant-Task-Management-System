"""
Router for managing business unit configurations.
This module provides endpoints to create, read, update, and delete configurations.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status

from app.backend.dependencies import get_auth_service
from app.backend.schemas.auth import (
    RegisterRequest,
    RegisterResponse, 
    LoginRequest,
    TokenResponse
)

# Initialize logger
logger = logging.getLogger(__name__)

# Define the API router
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    summary="Register a new user"
)
async def register_user(
    request: RegisterRequest,
    auth_service=Depends(get_auth_service)) -> RegisterResponse:
    """
    Register a new user with the provided email, password, and full name.
    
    Parameters
    ----------
    request : RegisterRequest
        The registration request containing email, password, and full name.

    Returns
    -------
    RegisterResponse
        A response indicating the success of the registration.
    """
    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        return RegisterResponse(message=f"User {user.email} registered successfully")
    except HTTPException as e:
        logger.error(f"Registration failed: {e.detail}")
        raise e


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login a user"
)
async def login_user(
    request: LoginRequest,
    auth_service=Depends(get_auth_service)) -> TokenResponse:
    """
    Authenticate a user and return access and refresh tokens.
    """
    try:
        tokens = await auth_service.login(
            email=request.email,
            password=request.password
        )
        return tokens
    except HTTPException as e:
        logger.error(f"Registration failed: {e.detail}")
        raise e
