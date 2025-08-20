from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, Type, Iterable

def dict_comparator(expected: Dict[str, Type], received: Dict[str, Type]) -> None:
    """
    compare two dict type collections
    """
    for key, elem in expected.items():
        rec_value = received.get(key, None)
        if rec_value is None:
            raise AssertionError
        assert rec_value == elem

async def get_objects_by_ids(session: AsyncSession, alchemy_model: Any, ids: Iterable[int]):
    """
    return scalars of some model by ids
    """
    stmt = (
        select(alchemy_model).filter(alchemy_model.id.in_(ids))
    )
    result = await session.execute(stmt)
    objects = result.scalars().all()
    return objects
    

