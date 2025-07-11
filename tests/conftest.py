from typing import AsyncGenerator
import pytest
from typing import AsyncGenerator
import asyncpg
from httpx import AsyncClient, ASGITransport

from decouple import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.database import get_async_session
from main import app
# from db.database import engine
from db.dbbase import Base
from api.auth import current_admin_user, current_user
from models.user import User
from db.types import Role
from decouple import config

DATABASE_URL = config('TEST_DB_URL')

test_engine = create_async_engine(DATABASE_URL)
TestingSessionMaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


pytest_plugins = [
    "tests.fixtures.course_fixtures",
    "tests.fixtures.user_fixtures"
]


DATABASE_URL = config('TEST_DB_URL')

test_engine = create_async_engine(
    DATABASE_URL,
)

TestingSessionMaker = async_sessionmaker(
    test_engine
)

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
    async with TestingSessionMaker() as session:
        yield session


@pytest.fixture(scope="function")
def override_session_dependency(session: AsyncSession):
    async def override_get_async_session():
        yield session

    app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture
async def client(override_session_dependency) -> AsyncGenerator[AsyncClient, None]:

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


@pytest.fixture(autouse=True)
def auto_override_user(request):
    mark = request.node.get_closest_marker("role")
    role = Role.ADMIN
    is_superuser = True

    if mark:
        role_name = mark.args[0]
        if role_name == 'student':
            role = Role.STUDENT
            is_superuser = False
        elif role_name == 'teacher':
            role = Role.TEACHER
            is_superuser = False
        elif role_name == 'admin':
            role = Role.ADMIN
            is_superuser = True

    async def override_user():
        return User(
            id=1,
            email=f"{role.lower()}@test.com",
            role=role,
            is_active=True,
            is_superuser=is_superuser
        )

    app.dependency_overrides[current_user] = override_user
    yield
    app.dependency_overrides.pop(current_user, None)
