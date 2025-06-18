from datetime import datetime
from pydantic import BaseModel

from models.course import Course



class CouseResponse(BaseModel):
    id: int
    name: str
    price: float
    #временно
    language_id:int
    level_id:int

    description: str
    created_at: datetime

    class Config:
        orm_mode = True

class CourseCreate(BaseModel):
    name: str
    price: float
    language_id: int
    level_id: int
    description: str

class LevelResponse(BaseModel):
    pass