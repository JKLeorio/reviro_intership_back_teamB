from datetime import datetime, time, date
from typing import Optional
from pydantic import BaseModel


class ClassroomBase(BaseModel):
    name: str


class ClassroomRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None


class ClassroomCreate(ClassroomBase):
    pass


class LessonRead(BaseModel):
    id: int
    name: str
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    group_id: int
    group_name: Optional[str] = None
    classroom: ClassroomRead
    created_at: datetime

    class Config:
        from_attributes = True


class LessonBase(BaseModel):

    name: str
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    group_id: int
    classroom_id: int


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    name: Optional[str] = None
    day: Optional[date] = None
    lesson_start: Optional[time] = None
    lesson_end: Optional[time] = None
    teacher_id: Optional[int] = None
    group_id: Optional[str] = None
    classroom_id: Optional[str] = None


class HomeworkRead(BaseModel):
    id: int
    created_at: datetime
    description: str
    lesson: LessonRead


class HomeworkBase(BaseModel):
    description: str
    lesson_id: int


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkUpdate(BaseModel):
    description: Optional[str] = None
    lesson_id: Optional[int] = None
