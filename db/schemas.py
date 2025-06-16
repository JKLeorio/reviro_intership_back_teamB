from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, FilePath
from typing import Optional, List
from fastapi_users import schemas
from .types import Role, Gender, Level


class UserCreate(schemas.BaseUserCreate):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(Role.STUDENT)


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    is_active: bool
    phone_number: Optional[str] = None


class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = Field(
        Role.STUDENT,
        description="User role, default is 'STUDENT'")


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=254)
    phone_number: Optional[str] = Field(
        None, description="User's phone number")
    sex: Optional[Gender] = None
    birth_date: Optional[datetime] = Field(
        None, description="User's birth date, iso 8601 format")

class SuperAdminCreate(schemas.BaseUserCreate):
    is_superuser: bool = True
    is_active: bool = True
    is_verified: bool = True
    role: Role = Role.ADMIN