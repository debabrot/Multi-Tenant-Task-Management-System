"""Dependencies for FastAPI application"""

from functools import lru_cache
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.core.config import settings, Settings
from app.backend.core.database import get_db
from app.backend.core.security import SecurityManager
from app.backend.services.auth_service import AuthService


@lru_cache
def get_settings() -> Settings:
    return settings


def get_security_manager(settings: Settings=Depends(get_settings)) -> SecurityManager:
    return SecurityManager(settings)


async def get_auth_service(
        db: Session=Depends(get_db),
        security_manager: SecurityManager=Depends(get_security_manager),
        settings: Settings=Depends(get_settings)) -> AuthService:
    if not db:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    if not security_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security manager not initialized"
        )
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings not initialized"
        )
    return AuthService(db, security_manager, settings=settings)
