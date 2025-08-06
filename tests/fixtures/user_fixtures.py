import pytest
from typing import Callable, Dict, Awaitable, Type
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from tests.fixtures.factories.models.user_factory import UserFactory
from tests.fixtures.utils import modern_factory_of_factories

@pytest.fixture
async def user_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def user(level_data : Dict[str, Type]) -> int:
        user = User(**level_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id
    return user

@pytest.fixture
async def modern_user_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(UserFactory, session)