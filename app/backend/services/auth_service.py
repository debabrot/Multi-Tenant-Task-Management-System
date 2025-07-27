"""Authentication Service"""
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.backend.core.config import Settings
from app.backend.models.user import User
from app.backend.core.security import SecurityManager


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

    async def login(self, email: str, password: str) -> dict:
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

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }