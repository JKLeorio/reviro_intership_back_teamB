from typing import Optional
from pydantic import BaseModel, ConfigDict, HttpUrl
from schemas.lesson import LessonBase
from schemas.user import UserBase

class SheduleLesson(LessonBase):
    id: int
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
