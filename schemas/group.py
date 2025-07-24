from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from db.types import PaymentDetailStatus, PaymentStatus
from schemas.course import CourseRead
from schemas.user import StudentResponse, TeacherResponse, UserResponse


class GroupBase(BaseModel):
    id: int
    name: str
    created_at: datetime
    start_date: date
    end_date: date
    is_active: bool
    is_archived: bool
    course_id: int
    teacher_id: int

    model_config = ConfigDict(from_attributes=True)


class GroupResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    start_date: date
    end_date: date
    is_active: bool
    is_archived: bool
    # временно
    course_id: int
    # course: CourseRead
    teacher: TeacherResponse
    teacher_id: int

    model_config = ConfigDict(from_attributes=True)


class GroupTeacherProfileResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_active: bool
    student_count: int


class GroupCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool
    is_archived: bool
    course_id: int
    teacher_id: int


class GroupUpdate(GroupCreate):
    pass


class GroupPartialUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    course_id: Optional[int] = None
    teacher_id: Optional[int] = None


class GroupStudentResponse(GroupResponse):
    students: List[StudentResponse]


class GroupStudentUpdate(GroupUpdate):
    students: List[int]


class GroupStundentPartialUpdate(GroupPartialUpdate):
    students: Optional[List[int]]


class GroupStudentDetailResponse(BaseModel):
    student: StudentResponse
    payment_status: PaymentDetailStatus
    attendance_ratio: float
    