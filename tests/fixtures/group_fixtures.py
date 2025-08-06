from typing import Awaitable, Callable, Dict, Type
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.group import Group
from tests.fixtures.factories.models.group_factory import GroupFactory
from tests.fixtures.utils import modern_factory_of_factories

@pytest.fixture
async def group_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def group(group_data : Dict[str, Type]) -> int:
        group = Group(**group_data)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group.id
    return group

@pytest.fixture
async def modern_group_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    return modern_factory_of_factories(GroupFactory, session)