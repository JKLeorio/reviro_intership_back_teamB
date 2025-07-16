from datetime import date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, HttpUrl
from schemas.lesson import ClassroomBase, LessonBase
from schemas.user import UserBase

class SheduleClassroom(ClassroomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class SheduleLesson(BaseModel):
    id: int
    name: str
    description: str
    link: Optional[HttpUrl]
    day: date
    lesson_start: time
    lesson_end: time
    teacher: UserBase
    classroom: SheduleClassroom

    model_config = ConfigDict(from_attributes=True)

class SheduleGroup(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
    

class SheduleItem(BaseModel):
    group: SheduleGroup
    lessons: list[SheduleLesson]

class SheduleResponse(BaseModel):
    MON: Optional[list[SheduleItem]] = None
    TUE: Optional[list[SheduleItem]] = None
    WED: Optional[list[SheduleItem]] = None
    THU: Optional[list[SheduleItem]] = None
    FRI: Optional[list[SheduleItem]] = None
    SAT: Optional[list[SheduleItem]] = None
    SUN: Optional[list[SheduleItem]] = None
