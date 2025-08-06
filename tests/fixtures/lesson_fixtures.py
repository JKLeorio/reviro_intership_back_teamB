from typing import Awaitable, Callable, Dict, Type
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.lesson import Classroom, Lesson
from schemas.lesson import AttendanceResponse, ClassroomRead, LessonRead
from schemas.shedule import SheduleLesson

from tests.fixtures.factories.models.lesson_factory import ClassroomFactory, LessonFactory

from db.database import get_async_session_context
from tests.fixtures.utils import modern_factory_of_factories

@pytest.fixture
async def lesson_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def lesson(lesson_data : Dict[str, Type]) -> Dict:
        lesson = Lesson(**lesson_data)
        session.add(lesson)
        await session.commit()
        await session.refresh(lesson, attribute_names=['teacher', 'classroom'])
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

@pytest.fixture
async def modern_lesson_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(LessonFactory, session)

@pytest.fixture
async def modern_classroom_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(ClassroomFactory, session)