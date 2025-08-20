from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LanguageRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageBase(BaseModel):
    name: str


class LanguageUpdate(BaseModel):
    name: Optional[str] = None


class LevelRead(BaseModel):
    id: int
    code: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LevelBase(BaseModel):
    code: str
    description: Optional[str] = None


class LevelUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None


class CourseRead(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None
    language_id: int
    level_id: int
    language_name: Optional[str] = None
    level_code: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CourseShortResponse(BaseModel):
    id: int
    name: str

class CourseBase(BaseModel):

    name: str
    price: float
    language_name: str
    level_code: str
    description: str | None = None


class CourseRelationBase(BaseModel):
    id: int
    name: str
    price: float
    language_id: int
    level_id: int
    description: str | None = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    language_id: Optional[int] = None
    level_id: Optional[int] = None


class ProfileCourse(BaseModel):
    id: int
    name: str
    language_name: str
    level_code: str