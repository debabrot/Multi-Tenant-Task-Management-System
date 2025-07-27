"""Main entrypoint for the task management API"""

from fastapi import FastAPI

from app.backend.routers import auth, users
from app.backend.utils.logger import setup_logging

# Set up logging
setup_logging()


app = FastAPI(
    title="Task Managemer API",
    version="1.0.0",
    description="API for managing tasks"
)
app.include_router(auth.router)
app.include_router(users.router)
