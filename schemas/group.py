from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

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
