from datetime import datetime, time, date
from typing import Optional, List
from pydantic import BaseModel, model_validator, ConfigDict, HttpUrl
from fastapi import UploadFile, File


def validate_time_func(values: dict):
    start = values.get('lesson_start')
    end = values.get('lesson_end')

    if start and end and start >= end:
        raise ValueError('lesson_start must be before lesson_end')

    return values


class ClassroomBase(BaseModel):
    name: str


class ClassroomRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None


class ClassroomCreate(ClassroomBase):
    pass


class LessonRead(BaseModel):
    id: int
    name: str
    description: str
    link: Optional[HttpUrl]
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    group_id: int
    classroom_id: int
    group_name: Optional[str] = None
    classroom_name: Optional[str] = None
    created_at: datetime

    homework: Optional['HomeworkRead']

    model_config = ConfigDict(from_attributes=True)


class LessonShort(BaseModel):
    name: str
    day: date


class LessonBase(BaseModel):
    name: str
    description: str
    link: Optional[HttpUrl] = None
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    # group_id: int
    classroom_id: int



class LessonCreate(LessonBase):
    @model_validator(mode='before')
    @classmethod
    def validate_time(cls, values):
        return validate_time_func(values)


class LessonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    day: Optional[date] = None
    link: Optional[HttpUrl] = None
    lesson_start: Optional[time] = None
    lesson_end: Optional[time] = None
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None
    classroom_id: Optional[int] = None

    @model_validator(mode='before')
    @classmethod
    def validate_time(cls, values):
        return validate_time_func(values)

    model_config = ConfigDict(from_attributes=True)


class HomeworkRead(BaseModel):
    id: int
    created_at: datetime
    deadline: date
    description: str
    lesson_id: int


class HomeworkBase(BaseModel):

    deadline: date
    description: str


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkUpdate(BaseModel):
    description: Optional[str] = None
    deadline: Optional[date] = None
    lesson_id: Optional[int] = None


class HomeworkSubmissionRead(BaseModel):
    id: int
    homework_id: int
    student_id: int
    file_path: Optional[str] = None
    content: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HomeworkSubmissionUpdate(BaseModel):
    content: Optional[str] = None


class HomeworkReviewCreate(BaseModel):
    submission_id: int
    comment: Optional[str] = None


class HomeworkReviewRead(BaseModel):
    id: int
    submission_id: int
    teacher_id: int
    comment: Optional[str] = None
    reviewed_at: date

    model_config = ConfigDict(from_attributes=True)


class HomeworkReviewUpdate(HomeworkReviewCreate):
    pass
