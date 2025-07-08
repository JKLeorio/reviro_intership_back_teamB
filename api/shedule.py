from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import (
    optional_current_user, 
    current_user, 
    current_admin_user, 
    current_teacher_user
    )

from fastapi_filter import FilterDepends
from fastapi_filter.contrib.sqlalchemy import Filter

from db.database import get_async_session
from models.user import User

shedule_router = APIRouter()





@shedule_router.get(
    '/',
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def shedule_global(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends()
):
    pass