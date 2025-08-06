from collections import defaultdict
from typing import Dict, List
from fastapi import APIRouter, Depends, status, HTTPException

import calendar
import datetime

from sqlalchemy import Sequence, select
from sqlalchemy.orm import selectinload, with_loader_criteria, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import (
    optional_current_user, 
    current_user, 
    current_admin_user, 
    current_teacher_user,
    current_student_user
    )

from fastapi_filter import FilterDepends
from fastapi_filter.contrib.sqlalchemy import Filter

from db.database import get_async_session
from db.types import Role
from models.group import Group
from models.lesson import Lesson
from models.user import User
from models.course import Course
from schemas.lesson import LessonBase
from schemas.shedule import SheduleGroup, SheduleLesson, SheduleResponse
from utils.date_time_utils import get_current_time, get_week_start_end

shedule_router = APIRouter()


# current_calendar = calendar.Calendar()



def format_shedule(groups_lessons: Sequence[Group]) -> Dict:
    '''
    format orm result into response
    '''
    buff_dict = defaultdict(list)
    result_dict = defaultdict(list)
    group_lessons: Group
    lesson: Lesson
    if groups_lessons is None:
        return SheduleResponse().model_dump()
    for group_lessons in groups_lessons:
        for lesson in group_lessons.lessons:
            week_day = calendar.day_abbr[lesson.day.weekday()].upper()
            buff_dict[week_day].append(SheduleLesson.model_validate(lesson))
    
        for week_day, lessons in buff_dict.items():
            result_dict[week_day].append(
                {
                'group' : SheduleGroup.model_validate(group_lessons),
                'lessons' : lessons
                }
            )
        buff_dict.clear()

    return result_dict



async def get_global_shedule(session: AsyncSession):
    '''
    get global shedule for current week
    '''
    week_start, week_end = get_week_start_end()
    stmt = (
    select(Group)
    .options(
        joinedload(Group.teacher),
        joinedload(Group.course).options(
            joinedload(Course.language),
            joinedload(Course.level)
        ),
        joinedload(Group.lessons).options(
            joinedload(Lesson.teacher),
            joinedload(Lesson.classroom)
        ),
    )
    .options(
        with_loader_criteria(
            Lesson,
            lambda cls:
                (cls.day.between(week_start, week_end)),
            include_aliases=True
        )
    )
    .join(Group.lessons)
    .where(
        Group.is_archived.is_(False),
        Lesson.day.between(week_start, week_end)
        )
    )
    result = await session.execute(stmt)
    groups_lessons = result.scalars().unique().all()

    return groups_lessons


async def get_student_shedule(student_id, session: AsyncSession):
    '''
    get student shedule for current week
    '''
    week_start, week_end = get_week_start_end()
    stmt = (
    select(Group)
    .options(
        joinedload(Group.teacher),
        joinedload(Group.course).options(
            joinedload(Course.language),
            joinedload(Course.level)
        ),
        joinedload(Group.lessons).options(
            joinedload(Lesson.teacher),
            joinedload(Lesson.classroom)
        ),
    )
    .options(
        with_loader_criteria(
            Lesson,
            lambda cls:
                (cls.day.between(week_start, week_end)),
            include_aliases=True
        )
    )
    .join(Group.lessons)
    .where(
        Group.is_archived.is_(False),
        Group.students.any(User.id == student_id),
        Lesson.day.between(week_start, week_end)
        )
    )
    result = await session.execute(stmt)
    groups_lessons = result.scalars().unique().all()
    return groups_lessons


async def get_group_shedule(group_id: int,session: AsyncSession):
    '''
    get group shedule for current week
    '''
    week_start, week_end = get_week_start_end()
    stmt = (
    select(Group)
    .options(
        joinedload(Group.teacher),
        joinedload(Group.course).options(
            joinedload(Course.language),
            joinedload(Course.level)
        ),
        joinedload(Group.lessons).options(
            joinedload(Lesson.teacher),
            joinedload(Lesson.classroom)
        ),
    )
    .options(
        with_loader_criteria(
            Lesson,
            lambda cls:
                (cls.day.between(week_start, week_end)),
            include_aliases=True
        )
    )
    .join(Group.lessons)
    .where(
        Group.is_archived.is_(False),
        Group.id == group_id,
        Lesson.day.between(week_start, week_end)
        )
    )
    result = await session.execute(stmt)
    groups_lessons = result.scalars().unique().all()
    return groups_lessons


async def get_teacher_shedule(teacher_id: int, session: AsyncSession):
    '''
    get teacher shedule for current week
    '''
    week_start, week_end = get_week_start_end()
    stmt = (
    select(Group)
    .options(
        joinedload(Group.teacher),
        joinedload(Group.course).options(
            joinedload(Course.language),
            joinedload(Course.level)
        ),
        joinedload(Group.lessons).options(
            joinedload(Lesson.teacher),
            joinedload(Lesson.classroom)
        ),
    )
    .options(
        with_loader_criteria(
            Lesson,
            lambda cls: (cls.teacher_id == teacher_id) &
                        (cls.day.between(week_start, week_end)),
            include_aliases=True
        )
    )
    .join(Group.lessons)
    .where(
        Group.is_archived.is_(False),
        Lesson.teacher_id == teacher_id,
        Lesson.day.between(week_start, week_end)
        )
    )
    result = await session.execute(stmt)
    groups_lessons = result.unique().scalars().all()
    return groups_lessons

@shedule_router.get(
    '/',
    response_model=SheduleResponse,
    status_code=status.HTTP_200_OK
)
async def shedule_global(
    session: AsyncSession = Depends(get_async_session),
    user: User|None = Depends(optional_current_user)
):
    '''
    Returns global shedule of all groups for current_week
    '''
    result = await get_global_shedule(session=session)
    shedule = format_shedule(result)
    return shedule


@shedule_router.get(
    '/my',
    response_model=SheduleResponse,
    status_code=status.HTTP_200_OK
)
async def shedule_user(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_student_user)
):
    '''
    Returns current user shedule for current week
    '''
    result=None
    
    if user.role == Role.STUDENT:
        result = await get_student_shedule(user.id, session)
    elif user.role == Role.TEACHER:
        result = await get_teacher_shedule(user.id, session)
    elif user.role == Role.ADMIN:
        #Временно
        result = await get_teacher_shedule(user.id, session)
    shedule = format_shedule(result)
    return shedule


@shedule_router.get(
        '/student/{user_id}',
        response_model=SheduleResponse,
        status_code=status.HTTP_200_OK
        )
async def shedule_by_student(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_teacher_user),
):
    '''
    Returns student shedule by user id for current week
    '''
    request_user = await session.get(User, user_id)
    if request_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found'
            )
    result = await get_student_shedule(user_id, session)
    shedule = format_shedule(result)
    return shedule


@shedule_router.get(
    '/group/{group_id}',
    response_model=SheduleResponse,
    status_code=status.HTTP_200_OK
    )
async def shedule_by_group(
    group_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_teacher_user)
    ):
    '''
    get group shedule by group id for current week
    '''
    group = await session.get(Group, group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='group not found'
            )
    result = await get_group_shedule(group_id, session)
    shedule = format_shedule(result)
    return shedule
