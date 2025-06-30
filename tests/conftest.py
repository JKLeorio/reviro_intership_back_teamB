import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from db.database import engine
from db.dbbase import Base
from api.auth import current_admin_user
from models.user import User
from db.types import Role


@pytest.fixture(scope='session')
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def override_admin_dependency():
    async def get_override_admin():
        return User(id=1, email="admin@gmail.com", role=Role.ADMIN, is_active=True, is_superuser=True)

    app.dependency_overrides[current_admin_user] = get_override_admin


@pytest.fixture
async def client(override_admin_dependency):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client
