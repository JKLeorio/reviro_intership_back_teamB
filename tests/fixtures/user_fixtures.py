import pytest
from typing import Callable, Dict, Awaitable, Type
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

@pytest.fixture
async def user_factory(session: AsyncSession) -> Callable[[Dict[str, type]], Awaitable[int]]:
    async def user(level_data : Dict[str, Type]) -> int:
        user = User(**level_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id
    return user