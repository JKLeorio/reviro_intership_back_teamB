from typing import Dict, Type, Callable, Awaitable
import pytest
from models.course import Course, Level, Language
from sqlalchemy.ext.asyncio import AsyncSession

from models.lesson import HomeworkSubmission
from schemas.course import LanguageRead, LevelRead
from schemas.lesson import LessonRead
from tests.fixtures.factories.models.course_factory import CourseFactory, LanguageFactory, LevelFactory
from tests.fixtures.factories.models.factory import FactorySessionController
from tests.fixtures.factories.models.group_factory import GroupFactory
from tests.fixtures.factories.models.lesson_factory import HomeworkFactory, HomeworkSubmissionFactory, LessonFactory
from tests.fixtures.factories.models.user_factory import UserFactory
from tests.fixtures.utils import modern_factory_of_factories

@pytest.fixture
async def course_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def course(course_data : Dict[str, Type]) -> int:
        course = Course(**course_data)
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return course.id
    return course

@pytest.fixture
async def language_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def language(language_data : Dict[str, Type]) -> int:
        language: Language = Language(**language_data)
        session.add(language)
        await session.commit()
        await session.refresh(language)
        return language.id
    return language

@pytest.fixture
async def level_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def level(level_data : Dict[str, Type]) -> int:
        level = Level(**level_data)
        session.add(level)
        await session.commit()
        await session.refresh(level)
        return level.id
    return level

@pytest.fixture
async def modern_course_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(CourseFactory, session)

@pytest.fixture
async def modern_language_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(LanguageFactory, session)

@pytest.fixture
async def modern_level_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(LevelFactory, session)


