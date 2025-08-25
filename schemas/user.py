from datetime import datetime
import re
from typing import Dict, List, Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field, ConfigDict, PrivateAttr, field_validator, model_validator
from fastapi_users import schemas

from db.types import PaymentDetailStatus, Role
from schemas.course import CourseShortResponse, ProfileCourse
from schemas.pagination import Pagination

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
    description: Optional[str] = None

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
    email: EmailStr


class UserPartialUpdate(schemas.CreateUpdateDictModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone_number: Optional[str] = Field(
        None, description="User's phone number")
    email: Optional[EmailStr] = None
    description: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    is_active: bool


class UserFullnameResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: Optional[str] = None
    role: Role
    is_active: bool

    model_config = ConfigDict(from_attributes=True)



class TeacherResponse(UserResponse):
    role: str
    description: str | None = None


class StudentTeacherRegister(UserRegister):
    role: Literal[Role.STUDENT, Role.TEACHER] = Role.STUDENT


class StudentTeacherCreate(UserCreate):
    phone_number: Optional[str] = None
    role: Role = Role.STUDENT
    description: Optional[str] = None


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


def validate_full_name(full_name: str) -> Dict[str, str]:
    parts = full_name.strip().split()
        
    if len(parts) < 2:
        raise ValueError("fullname must contain first and last names")

    pattern = re.compile(r"^[A-Za-zА-Яа-яЁё-]+$")
    for part in parts:
        if not pattern.match(part):
            raise ValueError(f"this name part doesn't correct: {part}")

    last_name, first_name = parts[1], parts[0]
    # middle_name = parts[2] if len(parts) > 2 else None
    return {
        'first_name' : first_name,
        'last_name' : last_name
    }

class SuperAdminUpdate(schemas.BaseUserUpdate):
    pass


class AdminRegister(UserRegister):
    role: Literal[Role.ADMIN] = Role.ADMIN


class TeacherProfile(UserBase):
    courses: list[ProfileCourse] = []

class StudentProfile(UserBase):
    courses: list[ProfileCourse] = []

class UserFullNameRegister(BaseModel):
    full_name: str
    
    _first_name: Optional[str] = PrivateAttr(default=None)
    _last_name: Optional[str] = PrivateAttr(default=None)

    email: EmailStr = Field(..., max_length=254)
    phone_number: str = None

    @model_validator(mode='after')
    def validate_full_name_field(self):
        if self.full_name is not None:
            names = validate_full_name(self.full_name)
            self._first_name = names['first_name']
            self._last_name = names['last_name']
        return self
    
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        if self.full_name is not None:
            data["first_name"] = self._first_name
            data["last_name"] = self._last_name
        return data

class UserFullNameUpdate(UserFullNameRegister):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None

class StudentRegister(UserFullNameRegister):
    role: Literal[Role.STUDENT] = Role.STUDENT

class TeacherFullNameResponse(UserFullnameResponse):
    description: str | None = None


class TeacherRegister(UserFullNameRegister):
    role: Literal[Role.TEACHER] = Role.TEACHER
    description: Optional[str] = None

class TeacherWithGroupResponse(TeacherFullNameResponse):
    group_id: int

class TeacherWithCourseResponse(TeacherFullNameResponse):
    courses: list[CourseShortResponse]

class TeachersWithCourseAndPagination(BaseModel):
    teachers : list[TeacherWithCourseResponse]
    pagination: Pagination