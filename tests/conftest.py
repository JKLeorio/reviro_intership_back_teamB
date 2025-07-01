from typing import AsyncGenerator
import pytest
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


pytest_plugins = [
    "tests.fixtures.course_fixtures"
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


@pytest.fixture(scope="session", autouse=True)
def override_admin_dependency():
    async def get_override_admin():
        return User(id=1, email="admin@gmail.com", role=Role.ADMIN, is_active=True, is_superuser=True)
    app.dependency_overrides[current_admin_user] = get_override_admin
    app.dependency_overrides[current_user] = get_override_admin

@pytest.fixture(scope="function")
def override_session_dependency(session: AsyncSession):
    async def override_get_async_session():
        yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

@pytest.fixture
async def client(override_admin_dependency, override_session_dependency):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client
