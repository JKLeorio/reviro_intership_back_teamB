from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_filter.base.filter import FilterDepends
from fastapi_filter.contrib.sqlalchemy import Filter

from db.database import get_async_session
from api.auth import current_teacher_user
from db.types import AttendanceStatus, Role
from models.user import User
from models.lesson import Attendance, Lesson
from schemas.lesson import AttendanceCreate, AttendancePartialUpdate, AttendanceResponse, AttendanceUpdate

from api.utils import validate_related_fields

attendance_router = APIRouter()


async def is_teacher_attendance_owner(
    user_id: int, 
    attendance_id: int,
    session: AsyncSession
):
    stmt = (
        select(Attendance)
        .options(
            selectinload(Attendance.lesson)
            .options(
                selectinload(Lesson.teacher)
            )
        ).join(
            Attendance.lesson,
        ).where(
            Attendance.id == attendance_id,
            Lesson.teacher_id == user_id
        )
    )
    result = await session.execute(stmt)
    attendance = result.scalar_one_or_none()
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you haven't permission"
            )
    return


class AttendanceFilter(Filter):
    status__in: Optional[list[AttendanceStatus]]

    class Constants(Filter.Constants):
        model = Attendance


# @attendance_router.get(
#     '/user/',
#     response_model=List[AttendanceResponse],
#     status_code=status.HTTP_200_OK
# )
# async def user_attendance(
#     user: User = Depends(current_teacher_user),

# ):
#     '''
#     RETURNS current user attendance 

#     ROLES: student, teacher or admin

#     STUDENT -> get own attendance

#     TEACHER -> doesn't get data

#     ADMIN -> doesn't get data
#     '''
#     pass

@attendance_router.get(
    '/student/{user_id}',
    response_model=List[AttendanceResponse],
    status_code=status.HTTP_200_OK
)
async def attendance_by_user(
    user_id: int,
    attendance_filter: AttendanceFilter = FilterDepends(AttendanceFilter),
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    RETURNS user attendance by user_id 

    ROLES: teacher or admin

    TEACHER -> has no restrictions

    ADMIN -> has no restrictions
    '''
    stmt = (
        select(Attendance)
        .where(Attendance.student_id == user_id)
    )
    filter_stmt = attendance_filter.filter(stmt)
    result = await session.execute(filter_stmt)
    attendance = result.scalars().all()
    return attendance


@attendance_router.get(
        '/{attendance_id}',
        response_model=AttendanceResponse,
        status_code=status.HTTP_200_OK
        )
async def attendance_detail(
    attendance_id: int,
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    RETURNS attendance detail data by attendance id

    ROLES: teacher or admin

    TEACHER -> has no restrictions

    ADMIN -> has no restrictions
    '''
    # if user.role == Role.TEACHER:
    #     is_teacher_attendance_owner(user.id, attendance_id, session)

    attendance = await session.get(Attendance, attendance_id)
    return attendance



@attendance_router.post(
    '/',
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED
)
async def attendance_create(
    attendance_data: AttendanceCreate,
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    CREATES attendance by sent data

    ROLES: teacher or admin

    TEACHER -> can update the attendance of only those lessons where he is the teacher

    ADMIN -> has no restrictions
    '''
    await validate_related_fields(
        {
            User : attendance_data.student_id,
            Lesson : attendance_data.lesson_id
        },
        session
    )
    attendance = Attendance(**attendance_data.model_dump())
    session.add(attendance)
    await session.commit()
    await session.refresh(attendance)
    return attendance




@attendance_router.put(
        '/{attendance_id}',
        response_model=AttendanceResponse,
        status_code=status.HTTP_200_OK
        )
async def attendance_update(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    UPDATES attendance by id with sent data

    ROLES: teacher or admin

    TEACHER -> can update the attendance of only those lessons where he is the teacher

    ADMIN -> has no restrictions
    '''
    attendance = await session.get(Attendance, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='attendance not found'
        )
    if user.role == Role.TEACHER:
        is_teacher_attendance_owner(user.id, attendance_id, session)

    await validate_related_fields(
        {
            User : attendance_data.student_id,
            Lesson : attendance_data.lesson_id
        },
        session
    )

    for key, value in attendance_data.model_dump().items():
        setattr(attendance,key,value)
    
    await session.commit()
    await session.refresh(attendance)
    return attendance




@attendance_router.patch(
        '/{attendance_id}',
        response_model=AttendanceResponse,
        status_code=status.HTTP_200_OK
        )
async def attendance_partial_update(
    attendance_id: int,
    attendance_data: AttendancePartialUpdate,
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    PARTIAL UPDATES attendance by id with sent data

    ROLES: teacher or admin

    TEACHER -> can update the attendance of only those lessons where he is the teacher

    ADMIN -> has no restrictions
    '''
    attendance = await session.get(Attendance, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='attendance not found'
        )
    
    if user.role == Role.TEACHER:
        is_teacher_attendance_owner(user.id, attendance_id, session)

    fields_for_validation = {}
    if attendance_data.student_id is not None:
        fields_for_validation[User] = attendance_data.student_id
    if attendance_data.lesson_id is not None:
        fields_for_validation[Lesson] = attendance_data.lesson_id

    await validate_related_fields(
        fields_for_validation,
        session
    )

    for key, value in attendance_data.model_dump(exclude_unset=True).items():
        setattr(attendance,key,value)
    
    await session.commit()
    await session.refresh(attendance)
    return attendance




@attendance_router.delete(
        '/{attendance_id}',
        status_code=status.HTTP_204_NO_CONTENT
        )
async def attendance_delete(
    attendance_id: int,
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    DELETES attendance by attendance id

    ROLES: teacher or admin

    TEACHER -> can delete the attendance of only those lessons where he is the teacher

    ADMIN -> has no restrictions
    '''
    if user.role == Role.TEACHER:
        is_teacher_attendance_owner(user.id, attendance_id, session)
    attendance = await session.get(Attendance, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='attendance not found'
            )
    await session.delete(attendance)
    return

# @attendance_router.get(
#     '/group/{group_id}',
#     response_model=List[AttendanceResponse],
#     status_code=status.HTTP_200_OK
# )
# async def user_attendance_by_group(
#     group_id,
#     user: User = Depends(current_teacher_user),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     '''
#     RETURNS student attendance in a group by group_id
#     '''
#     pass