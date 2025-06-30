from datetime import datetime
from typing import List, Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas

from db.types import Gender, Role

if TYPE_CHECKING:
    from schemas.group import GroupBase
    from schemas.lesson import HomeworkBase, LessonBase
    
#Используется для связей других схем
class UserBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    role: Role

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    # role: Role = Field(Role.STUDENT)

#Тут уже может быть вывод с вложенными полями,
#которые уже будут использовать чужие base модели
class UserResponse(UserBase):
    pass

class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    role: Role = Field(
        Role.STUDENT,
        description="User role, default is 'STUDENT'")
    phone_number: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str


class UserPartialUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=254)
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
    role: Role = Role.STUDENT

class AdminCreate(UserCreate):
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
    

class UserProfile(UserResponse):
    pass


class StudentProfile(UserProfile):

    
    groups_joined: List['GroupBase']
    # homeworks: List['HomeworkBase']
    lessons: List['LessonBase']

class TeacherProfile(UserProfile):

    
    groups_taught: List['GroupBase']
    # homeworks: List['HomeworkBase']
    # payments: List['PaymentBase']
    lessons: List['LessonBase']
