from datetime import datetime, time, date
from typing import Optional, List
from pydantic import BaseModel, model_validator, ConfigDict, HttpUrl
from fastapi import UploadFile, File


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

    homework: Optional['HomeworkBase']

    model_config = ConfigDict(from_attributes=True)


class LessonShort(BaseModel):
    name: str
    day: date


class LessonBase(BaseModel):
    id: int
    name: str
    description: str
    link: Optional[HttpUrl] = None
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    group_id: int
    classroom_id: int


class LessonCreate(BaseModel):
    name: str
    description: str
    link: Optional[HttpUrl] = None
    day: date
    lesson_start: time
    lesson_end: time
    teacher_id: int
    classroom_id: int

    @model_validator(mode='after')
    def validate_time(self) -> 'LessonCreate':
        if self.lesson_start >= self.lesson_end:
            raise ValueError('lesson_start must be before lesson_end')
        return self


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

    @model_validator(mode='after')
    def validate_time(self):
        if self.lesson_start and self.lesson_end:
            start = self.lesson_start.replace(tzinfo=None)
            end = self.lesson_end.replace(tzinfo=None)
            if start >= end:
                raise ValueError('lesson_start must be before lesson_end')
        return self

    model_config = ConfigDict(from_attributes=True)


class HomeworkRead(BaseModel):
    id: int
    created_at: datetime
    deadline: datetime
    file_path: Optional[str] = None
    description: Optional[str] = None
    lesson_id: int

    submissions: List["HomeworkSubmissionShort"] = []


class HomeworkSubmissionShort(BaseModel):
    id: int
    homework_id: int
    student_id: int
    file_path: Optional[str] = None
    content: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HomeworkBase(BaseModel):
    id: int
    deadline: datetime
    file_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HomeworkCreate(BaseModel):
    deadline: datetime
    description: Optional[str] = None
    file_path: Optional[str] = None


class HomeworkUpdate(BaseModel):
    description: Optional[str] = None
    deadline: Optional[date] = None
    lesson_id: Optional[int] = None


class HomeworkSubmissionRead(HomeworkSubmissionShort):
    review: Optional["HomeworkReviewShort"] = None


class HomeworkSubmissionUpdate(BaseModel):
    content: Optional[str] = None
    file_path: Optional[str] = None


class HomeworkReviewShort(BaseModel):
    id: int
    comment: str

    model_config = ConfigDict(from_attributes=True)


class HomeworkReviewCreate(BaseModel):
    comment: str


class HomeworkReviewRead(BaseModel):
    id: int
    submission_id: int
    teacher_id: int
    comment: str
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HomeworkReviewBase(BaseModel):
    comment: str

    model_config = ConfigDict(from_attributes=True)


class HomeworkReviewUpdate(HomeworkReviewBase):
    pass
