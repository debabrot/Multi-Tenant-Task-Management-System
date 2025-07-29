"""
Security utilities for the task-manager microservice.

Exports
-------
SecurityManager
    High-level wrapper around hashing, JWT creation/validation and refresh-token
    blacklisting.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt
from passlib.context import CryptContext

from app.backend.core.config import Settings

# Password hashing context
_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

class SecurityManager:
    """
    Handles password hashing/verification, JWT encoding/decoding and
    refresh-token blacklisting.
    """
    def __init__(self, settings: Settings):
        self._settings = settings
        self._blacklist_access: set[str] = set()
        self._blacklist_refresh: set[str] = set()

    @staticmethod
    def hash_password(plain: str) -> str:
        """Hash a plain-text password using Argon2."""
        return _pwd_ctx.hash(plain)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Return True if the plain password matches the stored hash."""
        return _pwd_ctx.verify(plain, hashed)
    
    async def revoke_access_token(self, token: str) -> None:
        """Add an access token to the blacklist (for logout)."""
        self._blacklist_access.add(token)
    
    async def revoke_refresh_token(self, token: str) -> None:
        """Add a refresh token to the blacklist."""
        self._blacklist_refresh.add(token)
    
    async def is_access_token_revoked(self, token: str) -> bool:
        """Check whether an access token has been revoked."""
        return token in self._blacklist_access
    
    async def is_refresh_token_revoked(self, token: str) -> bool:
        """Check whether a refresh token has been revoked."""
        return token in self._blacklist_refresh

    def decode_token(self, token: str) -> Dict[str, object]:
        """
        Decode and verify a JWT.

        Raises
        ------
        jwt.InvalidTokenError
            If signature, exp, nbf or other claim is invalid.
        """
        payload = jwt.decode(token, self._settings.JWT_SECRET_KEY, algorithms=[self._settings.JWT_ALGORITHM])
        # Check blacklist based on token type
        token_type = payload.get("type")
        if token_type == "access" and token in self._blacklist_access:
            raise jwt.InvalidTokenError("Access token has been revoked")
        elif token_type == "refresh" and token in self._blacklist_refresh:
            raise jwt.InvalidTokenError("Refresh token has been revoked")
        return payload

    def create_access_token(
        self,
        *,
        sub: uuid.UUID,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a short-lived access token.

        Parameters
        ----------
        sub : uuid.UUID
            The user id to encode inside the token.
        expires_delta : timedelta | None
            Optional custom lifetime.  If omitted, the class constant
            `ACCESS_TOKEN_EXPIRE_MINUTES` is used.

        Returns
        -------
        str
            Signed compact JWT.
        """
        now = datetime.now(timezone.utc)
        expire = now + (
            expires_delta or timedelta(minutes=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload: Dict[str, object] = {
            "exp": expire,
            "iat": now,
            "nbf": now,
            "sub": str(sub),
            "type": "access",
        }
        return jwt.encode(payload, self._settings.JWT_SECRET_KEY, algorithm=self._settings.JWT_ALGORITHM)

    def create_refresh_token(
        self,
        *,
        sub: uuid.UUID,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a long-lived refresh token.

        Parameters
        ----------
        sub : uuid.UUID
            The user id to encode inside the token.
        expires_delta : timedelta | None
            Optional custom lifetime.  If omitted, the class constant
            `REFRESH_TOKEN_EXPIRE_DAYS` is used.

        Returns
        -------
        str
            Signed compact JWT.
        """
        now = datetime.now(timezone.utc)
        expire = now + (
            expires_delta or timedelta(days=self._settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        payload: Dict[str, object] = {
            "exp": expire,
            "iat": now,
            "nbf": now,
            "sub": str(sub),
            "type": "refresh",
        }
        token = jwt.encode(payload, self._settings.JWT_SECRET_KEY, algorithm=self._settings.JWT_ALGORITHM)

        return token
