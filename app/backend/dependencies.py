"""Dependencies for FastAPI application"""

from uuid import UUID
from typing import Dict, Any

from functools import lru_cache
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError

from app.backend.core.config import settings, Settings
from app.backend.core.database import get_db
from app.backend.core.security import SecurityManager
from app.backend.services.auth_service import AuthService
from app.backend.services.user_service import UserService

# Initalize HTTPBearer for token authentication
http_bearer = HTTPBearer()


@lru_cache
def get_settings() -> Settings:
    return settings


def get_security_manager(settings: Settings=Depends(get_settings)) -> SecurityManager:
    return SecurityManager(settings)


async def get_auth_service(
        db: Session=Depends(get_db),
        security_manager: SecurityManager=Depends(get_security_manager),
        settings: Settings=Depends(get_settings)) -> AuthService:
    return AuthService(db, security_manager, settings=settings)


async def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """
    Dependency to get UserService instance.

    Parameters
    ----------
    db : Session
        Database session

    Returns
    -------
    UserService
        UserService instance
    """
    return UserService(db)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> UUID:
    return await auth_service.get_current_user_id(credentials)
