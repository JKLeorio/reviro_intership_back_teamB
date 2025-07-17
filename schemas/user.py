from datetime import datetime
from typing import List, Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from fastapi_users import schemas

from db.types import Role
from schemas.course import ProfileCourse

if TYPE_CHECKING:
    from schemas.group import GroupBase
    from schemas.lesson import HomeworkBase, LessonBase
    

class UserBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    role: Role

    model_config = ConfigDict(from_attributes=True)



class UserCreate(schemas.BaseUserCreate):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    # role: Role = Field(Role.STUDENT)


class UserResponse(UserBase):
    #временно
    password: Optional[str] = None

class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(
        Role.STUDENT,
        description="User role, default is 'STUDENT'")
    phone_number: Optional[str] = None

class UserUpdate(schemas.CreateUpdateDictModel):
    first_name: str
    last_name: str
    phone_number: str


class UserPartialUpdate(schemas.CreateUpdateDictModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone_number: Optional[str] = Field(
        None, description="User's phone number")


class StudentResponse(BaseModel):
    id: int
    first_name: str
    last_name: str


class TeacherResponse(UserResponse):
    role: str


class StudentTeacherRegister(UserRegister):
    role: Literal[Role.STUDENT, Role.TEACHER] = Role.STUDENT


class StudentTeacherCreate(UserCreate):
    phone_number: Optional[str] = None
    role: Role = Role.STUDENT


class AdminCreate(UserCreate):
    phone_number: Optional[str] = None
    role: Role = Role.ADMIN


class SuperAdminCreate(UserCreate):

    email: EmailStr
    password: str
    is_superuser: bool = Field(default=True)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=True)
    role: Role = Field(default=Role.ADMIN)


class SuperAdminUpdate(schemas.BaseUserUpdate):
    pass


class AdminRegister(UserRegister):
    role: Literal[Role.ADMIN] = Role.ADMIN


class TeacherProfile(UserBase):
    courses: list[ProfileCourse] = []

class StudentProfile(UserBase):
    courses: list[ProfileCourse] = []