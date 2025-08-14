import contextlib
import pytest
import shutil
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from db.database import get_async_session
from main import app
from db.dbbase import Base
from api.auth import current_user
from models.user import User
from db.types import Role
from decouple import config

from api.auth import current_super_user
from api.lesson import MEDIA_FOLDER, HOMEWORK_FOLDER

DATABASE_URL = config('TEST_DB_URL')

test_engine = create_async_engine(DATABASE_URL)
testing_session_maker = async_sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
    )


pytest_plugins = [
    "tests.fixtures.course_fixtures",
    "tests.fixtures.user_fixtures",
    "tests.fixtures.lesson_fixtures",
    "tests.fixtures.group_fixtures"
]

# @contextlib.asynccontextmanager
@pytest.fixture(scope='session')
async def session_session():
    async with testing_session_maker() as session:
        yield session

@pytest.fixture(scope='session')
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with testing_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def override_session_dependency(session: AsyncSession):
    async def override_get_async_session():
        yield session

    app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture
async def client(override_session_dependency) -> AsyncGenerator[AsyncClient, None]:

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

@pytest.fixture(scope='session', autouse=True)
async def users(session_session):
    session = session_session 

    super_admin = User(
        first_name = 'super_admin',
        last_name = 'super_admin',
        email = 'super@super.com',
        phone_number = '55544433321',
        role = Role.ADMIN,
        hashed_password = '',
        is_active = True,
        is_superuser = True,
        is_verified = True
        )
    
    admin = User(
        first_name = 'admin',
        last_name = 'admin',
        email = 'admin@admin.com',
        phone_number = '55544433322',
        role = Role.ADMIN,
        hashed_password = ''
        )
    teacher =  User(
        first_name = 'teacher',
        last_name = 'teacher',
        email = 'teacher@teacher.com',
        phone_number = '55544433323',
        role = Role.TEACHER,
        hashed_password = ''
        )
    student =  User(
        first_name = 'student',
        last_name = 'student',
        email = 'student@student.com',
        phone_number = '55544433324',
        role = Role.STUDENT,
        hashed_password = ''
        )
    session.add_all([super_admin, admin, teacher, student])
    await session.commit()
    await session.refresh(admin)
    await session.refresh(teacher)
    await session.refresh(student)
    await session.refresh(super_admin)
    
    return {
        "super_admin": super_admin,
        "admin": admin,
        "teacher": teacher,
        "student": student,
    }

    

@pytest.fixture(autouse=True)
async def auto_override_user(request, users):
    mark = request.node.get_closest_marker("role")
    user = users['admin']
    if mark:
        role_name = mark.args[0]
        if role_name == 'student':
            user = users['student']
        elif role_name == 'teacher':
            user = users['teacher']
        elif role_name == 'admin':
            user = users['admin']
        elif role_name == 'admin':
            user = users['super_admin']


    async def override_user():
        return user


    app.dependency_overrides[current_user] = override_user
    if mark and mark.args[0] == 'super_admin':
        app.dependency_overrides[current_super_user] = override_user
    yield
    app.dependency_overrides.pop(current_user, None)
    app.dependency_overrides.pop(current_super_user, None)


@pytest.fixture(autouse=True)
def patch_media_folders(monkeypatch, tmp_path):
    test_media_submissions = tmp_path / "homework_submissions"
    test_media_homeworks = tmp_path / "homeworks"

    test_media_submissions.mkdir()
    test_media_homeworks.mkdir()

    monkeypatch.setattr('api.lesson.MEDIA_FOLDER', str(test_media_submissions))
    monkeypatch.setattr('api.lesson.HOMEWORK_FOLDER', str(test_media_homeworks))

    yield
