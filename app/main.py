from fastapi import FastAPI
from app.backend.routers import auth


app = FastAPI(
    title="Task Managemer API",
    version="1.0.0",
    description="API for managing tasks"
)
app.include_router(auth.router)
