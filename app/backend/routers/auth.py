"""
Router for managing business unit configurations.
This module provides endpoints to create, read, update, and delete configurations.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.backend.dependencies import get_auth_service
from app.backend.services.auth_service import AuthService
from app.backend.schemas.auth import (
    RegisterRequest,
    RegisterResponse, 
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutResponse,
    LogoutRequest
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize HTTPBearer for token authentication
http_bearer = HTTPBearer()

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
    auth_service: AuthService=Depends(get_auth_service)) -> RegisterResponse:
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
    auth_service: AuthService=Depends(get_auth_service)) -> TokenResponse:
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


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate new access and refresh tokens using a valid refresh token"
)
async def refresh_token(
    refresh_request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.
    
    Parameters
    ----------
    refresh_request : RefreshTokenRequest
        Request containing the refresh token
    auth_service : AuthService
        Authentication service instance
        
    Returns
    -------
    TokenResponse
        New access and refresh tokens
        
    Raises
    ------
    HTTPException
        If refresh token is invalid or expired
    """
    try:
        tokens = await auth_service.refresh_tokens(refresh_request.refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description="Logout user and invalidate both access and refresh tokens"
)
async def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> LogoutResponse:
    """
    Logout user and invalidate both tokens.
    
    Parameters
    ----------
    request : LogoutRequest
        Contains the refresh token
    credentials : HTTPAuthorizationCredentials
        Bearer token credentials (access token)
    auth_service : AuthService
        Authentication service instance
        
    Returns
    -------
    LogoutResponse
        Success message
    """
    try:
        access_token = credentials.credentials
        refresh_token = request.refresh_token

        await auth_service.logout_user(access_token, refresh_token)
        return LogoutResponse(message="Successfully logged out")

    except HTTPException:
        # Re-raise HTTP exceptions from auth_service
        raise
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )