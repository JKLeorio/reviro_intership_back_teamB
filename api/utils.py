from typing import Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.dbbase import Base

async def validate_related_fields(models_ids: Dict[Base, int], session: AsyncSession):
    for model, m_id in models_ids.items():
        if not await session.get(model, m_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'detail':f'{model.__name__} not found'}
                )
    return