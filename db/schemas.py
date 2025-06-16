from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, FilePath
from typing import Optional, List
from fastapi_users import schemas
from .types import Role, Gender, Level


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(Role.STUDENT)


class UserResponse(BaseModel):
    id: int
    email: str
    role: Role
    is_active: bool
    is_admin: bool
    is_verified: bool


class UserRegister(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(
        Role.STUDENT,
        description="User role, default is 'student'")

class AdminRegister(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(
        Role.ADMIN,
        description="User role, default is 'admin'")

