from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True