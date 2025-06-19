from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas

from db.types import Gender, Role


class UserCreate(schemas.BaseUserCreate):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    # role: Role = Field(Role.STUDENT)


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    # role: Role = Field(
    #     Role.STUDENT,
    #     description="User role, default is 'STUDENT'")
    phone_number: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=254)
    phone_number: Optional[str] = Field(
        None, description="User's phone number")
    

class TeacherResponse(UserResponse):
    role: str


class SuperAdminCreate(schemas.BaseUserCreate):
    first_name: str = Field(default="Super")
    last_name: str = Field(default="Admin")
    is_superuser: bool = Field(default=True)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=True)
    role: Role = Field(default=Role.ADMIN)


class SuperAdminUpdate(schemas.BaseUserUpdate):
    pass

class AdminRegister(schemas.BaseUserCreate):
    first_name: str = Field(default="Just")
    last_name: str = Field(default="Admin")
    role: Literal[Role.ADMIN] = Role.ADMIN
    
