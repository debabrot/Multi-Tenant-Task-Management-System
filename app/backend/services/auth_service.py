"""Authentication Service"""
import logging
from typing import Dict, Any
from uuid import UUID


from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt import PyJWTError

from app.backend.core.config import Settings
from app.backend.models.user import User
from app.backend.core.security import SecurityManager
from app.backend.schemas.auth import RegisterRequest, TokenResponse


# Configure logger
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session, security_manager: SecurityManager, settings: Settings):
        self._db = db
        self._security_manager = security_manager
        self._settings = settings

    async def register(self, email: str, password: str, full_name: str) -> User:
        """
        Register a new user.

        Parameters
        ----------
        email : str
            The email of the new user.
        password : str
            The plain-text password of the new user.
        full_name : str
            The full_name of the new user.

        Returns
        -------
        User
            The newly created user object.
        """
        # Check if the email already exists
        existing_user = self._db \
            .query(User) \
            .filter(User.email == email) \
            .first()
        if existing_user:
            logger.error(f"User with email {email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists")

        # Hash the password
        hashed_password = self._security_manager.hash_password(password)

        # Create a new user
        new_user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name
        )
        self._db.add(new_user)
        self._db.commit()
        self._db.refresh(new_user)
        logger.info(f"User {email} registered successfully")

        return new_user

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate a user and return tokens.

        Parameters
        ----------
        email : str
            The email of the user.
        password : str
            The plain-text password of the user.

        Returns
        -------
        dict
            A dictionary containing the access token and refresh token.
        """
        # Find the user by email
        user = self._db\
            .query(User) \
            .filter(User.email == email) \
            .first()
        if not user or not self._security_manager.verify_password(password, user.password_hash):
            logger.error(f"Invalid credentials for user {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials")
        
        # Ensure user.id is explicitly converted to UUID
        user_id = UUID(str(user.id))

        # Create access and refresh tokens
        access_token = self._security_manager.create_access_token(sub=user_id)
        refresh_token = self._security_manager.create_refresh_token(sub=user_id)
        logger.info(f"User {email} logged in successfully")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access and refresh tokens using a valid refresh token.
        
        Parameters
        ----------
        refresh_token : str
            The refresh token to validate and use for generating new tokens
            
        Returns
        -------
        Dict[str, str]
            Dictionary containing new access_token and refresh_token
            
        Raises
        ------
        HTTPException
            If refresh token is invalid or expired
        """
        try:
            # Decode and validate the refresh token
            payload = self._security_manager.decode_token(refresh_token)

            # Check if token type is refresh
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # Check if user still exists
            user = self._db \
                .query(User) \
                .filter(User.id == user_id) \
                .first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Ensure user.id is explicitly converted to UUID
            user_id = UUID(str(user.id))

            # Check if refresh token is blacklisted (if you implement token blacklisting)
            if await self._security_manager.is_refresh_token_revoked(refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            # Generate new tokens
            new_access_token = self._security_manager.create_access_token(
                sub=user_id
            )
            new_refresh_token = self._security_manager.create_refresh_token(
                sub=user_id
            )

            await self._security_manager.revoke_refresh_token(refresh_token)

            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token
            )

        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
    
    async def logout_user(self, access_token: str, refresh_token: str) -> None:
        """
        Logout user by blacklisting their current access token.

        Parameters
        ----------
        access_token : str
            The access token to blacklist

        Raises
        ------
        HTTPException
            If token is invalid
        """
        try:
            # Validate tokens before blacklisting
            self._security_manager.decode_token(access_token)
            self._security_manager.decode_token(refresh_token)

            # Blacklist both tokens
            await self._security_manager.revoke_access_token(access_token)
            await self._security_manager.revoke_refresh_token(refresh_token)
            logger.info("User logged out successfully - tokens blacklisted")

        except PyJWTError:
            logger.info("Logout called with invalid tokens - treating as successful")
            await self._security_manager.revoke_access_token(access_token)
            await self._security_manager.revoke_refresh_token(refresh_token)

    async def get_current_user_id(
            self, credentials: HTTPAuthorizationCredentials) -> UUID:
        token = credentials.credentials
        try:
            if await self._security_manager.is_access_token_revoked(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            payload: Dict[str, Any] = self._security_manager.decode_token(token)
            user_id_str: Any = payload.get("sub")
            if user_id_str is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_id = UUID(user_id_str)
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type. Only access tokens are allowed for this endpoint.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user_id
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
