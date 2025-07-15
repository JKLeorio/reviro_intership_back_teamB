from typing import List, Optional, Union
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
from models.course import Course
from models.lesson import Lesson
from models.payment import Payment
from models.user import User, student_group_association_table
from models.group import Group
from schemas.course import ProfileCourse
from schemas.user import (
    StudentProfile,
    TeacherProfile,
    UserBase,
    UserPartialUpdate,
    UserResponse,
    UserUpdate
)

user_router = routing.APIRouter()



class UserFilter(Filter):
    role__in: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = User



async def get_teacher_profile_data(user_id, session: AsyncSession):
    user = await session.get(User, user_id)
    course_query = select(
        Course
        ).options(
            selectinload(Course.groups),
            selectinload(Course.language),
            selectinload(Course.level)
        ).join(
            Course.groups
        ).where(
            Group.is_archived.is_(False),
            Group.teacher_id == user_id
        ).distinct(Course.id)
    result = await session.execute(course_query)
    courses = result.scalars().all()

    profile_response = TeacherProfile.model_validate(user)
    profile_response.courses = [
        ProfileCourse(
            id=course.id, 
            name=course.name,
            language_name=course.language.name,
            level_code=course.level.code
            ) for course in courses
        ]
    return profile_response

async def get_student_profile_data(user_id, session: AsyncSession):
    user = await session.get(User, user_id)
    course_query = select(
        Course
        ).options(
            selectinload(Course.groups),
            selectinload(Course.language),
            selectinload(Course.level)
        ).join(
            Course.groups
        ).where(
            Group.is_archived.is_(False),
            Group.students.any(User.id == user_id)
        ).distinct(Course.id)
    result = await session.execute(course_query)
    courses = result.scalars().all()

    profile_response = StudentProfile.model_validate(user)
    profile_response.courses = [
        ProfileCourse(
            id=course.id, 
            name=course.name,
            language_name=course.language.name,
            level_code=course.level.code
            ) for course in courses
        ]
    return profile_response


@user_router.get(
        '/profile',
        response_model=Union[StudentProfile, TeacherProfile],
        status_code=status.HTTP_200_OK
)
async def user_profile(
    user: User = Depends(current_student_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Return current user profile data by the role
    '''
    if user.role == Role.STUDENT:
        return await get_student_profile_data(user.id, session)
    elif user.role == Role.TEACHER:
        return await get_teacher_profile_data(user.id, session)
    elif user.role == Role.ADMIN:
        #временно
        return await get_teacher_profile_data(user.id, session)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

@user_router.get(
    '/data', 
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def user_data(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
    ):
    '''
    Return current user data
    '''
    return user

@user_router.get(
    '/', 
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK
)
async def user_list(
    limit: int = 10,
    offset: int = 0,
    user_filter: UserFilter = FilterDepends(UserFilter),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
    ):
    '''
    Return list of users, admin only
    '''
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
    '''
    Return user detail data by user id, admin only
    '''
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
    '''
    Update user data by user id, admin only
    '''
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
async def user_partial_update(
    user_id: int,
    user_update: UserPartialUpdate,
    user_manager: UserManager = Depends(get_user_manager),
    user: User = Depends(current_admin_user)
):
    '''
    Partial update user data by user id, admin only
    '''
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
    '''
    Delete user by user id, admin only
    '''
    try:
        user_to_delete = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"detail": "User doesn't exist"}
            )
    await user_manager.delete(user=user_to_delete)
    return