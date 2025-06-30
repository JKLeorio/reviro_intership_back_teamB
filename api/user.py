from typing import List, Optional
from fastapi import routing, HTTPException, Depends, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.base.filter import FilterDepends

from fastapi_users.exceptions import UserNotExists

from db.database import get_async_session
from api.auth import (
    UserManager,
    current_user,
    current_student_user,
    current_teacher_user,
    current_admin_user,
    current_only_student_user,
    get_user_manager
    )


from db.types import Role
from models.lesson import Lesson
from models.payment import Payment
from models.user import User, student_group_association_table
from models.group import Group
from schemas.user import (
    # StudentProfile,
    # TeacherProfile,
    # TeacherResponse,
    UserPartialUpdate,
    UserResponse,
    UserUpdate
)

user_router = routing.APIRouter()

# teacher_router = routing.APIRouter()
# student_router = routing.APIRouter()


class UserFilter(Filter):
    role__in: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = User


# @teacher_router.get(
#         '/',
#         response_model=TeacherResponse,
#         status_code=status.HTTP_200_OK
#         )
# async def teacher_list(
#     session: AsyncSession = Depends(get_async_session)
# ):
#     pass


# @teacher_router.get(
#         '/profile',
#         response_model=TeacherProfile,
#         status_code=status.HTTP_200_OK
# )
# async def teacher_profile(
#     user: User = Depends(current_teacher_user),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     await session.refresh(user, attribute_names=['groups_taught'])
#     query = select(
#         Lesson
#         ).join(
#             Group
#             ).join(
#                 student_group_association_table,
#                 Group.id == student_group_association_table.c.group_id
#                 ).where(
#                     student_group_association_table.c.user_id == user.id
#                     )
    
#     lessons = session.execute(query)



# @student_router.get(
#         '/profile',
#         response_model=StudentProfile,
#         status_code=status.HTTP_200_OK
# )
# async def student_profile(
#     user: User = Depends(current_only_student_user),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     pass


@user_router.get(
    '/', 
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK
)
async def user_list(
    limit: int = 10,
    offset: int = 0,
    user_filter: UserFilter = FilterDepends(UserFilter),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
    ):
    query = user_filter.filter(
        select(User).offset(offset=offset).limit(limit=limit)
        )
    users = await session.execute(query)
    return users.scalars().all()


@user_router.get(
    '/{user_id}', 
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def user_detail(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    user = await session.get(
        User, 
        user_id, 
        # options=[
        #     selectinload(User.groups_joined),
        #     ]
            )
    if not user:
        raise HTTPException(
            detail={"detail": "User doesn't exist"},
            status_code=status.HTTP_404_NOT_FOUND
            )
    return user

@user_router.put(
    '/{user_id}',
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def user_update(
    user_id: int,
    user_update:  UserUpdate,
    user_manager: UserManager = Depends(get_user_manager),
    user: User = Depends(current_admin_user)
):
    try:
        old_user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"detail": "User doesn't exist"}
            )
    
    updated_user = await user_manager.update(user_update=user_update, user=old_user)
    return updated_user

@user_router.patch(
        '/{user_id}',
        response_model=UserResponse,
        status_code=status.HTTP_200_OK
)
async def user_update(
    user_id: int,
    user_update: UserPartialUpdate,
    user_manager: UserManager = Depends(get_user_manager),
    user: User = Depends(current_admin_user)
):
    try:
        old_user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"detail": "User doesn't exist"}
            )
    updated_user = await user_manager.update(user_update=user_update, user=old_user)
    return updated_user



@user_router.delete(
    '/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def user_delete(
    user_id: int,
    user_manager: UserManager = Depends(get_user_manager),
    user: User = Depends(current_admin_user)
):
    
    try:
        user_to_delete = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"detail": "User doesn't exist"}
            )
    await user_manager.delete(user=user_to_delete)
    return