from typing import Awaitable, Callable, Dict, Type
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.lesson import Classroom, Lesson
from schemas.shedule import SheduleLesson

@pytest.fixture
async def lesson_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def lesson(lesson_data : Dict[str, Type]) -> Dict:
        lesson = Lesson(**lesson_data)
        session.add(lesson)
        await session.commit()
        await session.refresh(lesson)
        return SheduleLesson.model_validate(lesson)
    return lesson


@pytest.fixture
async def classroom_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def classroom(classroom_data : Dict[str, Type]) -> int:
        classroom = Classroom(**classroom_data)
        session.add(classroom)
        await session.commit()
        await session.refresh(classroom)
        return classroom.id
    return classroom