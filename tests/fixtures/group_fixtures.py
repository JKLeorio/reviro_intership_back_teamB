from typing import Awaitable, Callable, Dict, Type
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.group import Group

@pytest.fixture
async def group_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def group(group_data : Dict[str, Type]) -> int:
        group = Group(**group_data)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group.id
    return group
