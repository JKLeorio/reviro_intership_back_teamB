from datetime import date, datetime
from pydantic import BaseModel


class GroupResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    start_date: date
    end_date: date
    is_active: bool
    is_archived: bool
    #временно
    course_id: int
    teacher_id: int

class GroupCreate(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_active: bool
    is_archived: bool
    course_id: int
    teacher_id: int