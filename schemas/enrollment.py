from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from models.enrollment import Enrollment
from schemas.course import CouseResponse

class EnrollmentResponse(BaseModel):
    id: int
    first_nme: str
    last_name: str
    created_at: datetime
    phone_number: Optional[str] = None
    is_approved: bool
    course: CouseResponse
    user_id: Optional[int]

    class Config:
        orm_mode = True


class EnrollmentCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str]
    course_id: int
    user_id: Optional[int]


class EnrollmentUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    course_id: Optional[int]
    user_id: Optional[int]