"""
Database Session Management Module.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from backend.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for providing a SQLAlchemy database session.

    Yields:
        Session: A SQLAlchemy database session that can be used within a request context.

    Ensures:
        The session is automatically closed after the request is completed,
        making it suitable for use with dependency injection frameworks like FastAPI.

    Example:
        ```
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()