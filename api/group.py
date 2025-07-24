from typing import List
from datetime import datetime, date
from fastapi import routing, HTTPException, Depends, status

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, joinedload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_session
from api.auth import (
    optional_current_user,
    current_user,
    current_student_user,
    current_teacher_user,
    current_admin_user
    )
from api.payment import create_initial_payment, inactivate_payment
from models.payment import PaymentDetail
from db.types import AttendanceStatus, PaymentDetailStatus, Role
from models.user import User, student_group_association_table
from models.group import Group
from models.course import Course
from schemas.group import (
    GroupCreate, 
    GroupResponse,
    GroupStudentDetailResponse,
    GroupStundentPartialUpdate,
    GroupTeacherProfileResponse, 
    GroupUpdate, 
    GroupPartialUpdate,
    GroupStudentResponse,
    GroupStudentUpdate
    )
from schemas.user import StudentResponse


group_router = routing.APIRouter()

#Удаление студента из группы, добавление в группу и т.д
group_students_router = routing.APIRouter()



# @group_students_router.get(
#         '/detail/{group_id}',
#         response_model=List[GroupStudentDetailResponse],
#         status_code=status.HTTP_200_OK
# )
# async def group_students_detail_list(
#     group_id: int,
#     user: User = Depends(current_teacher_user),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     '''
#     Returns a list of students by group with student attendance, payment status

#     ROLES -> teacher, admin

#     '''
#     group = await session.get(Group, group_id)
#     stmt = (
#         select(User)
#         .join(User.groups_joined)
#         .where(Group.id == group_id)
#         .options(
#             selectinload(User.payments),
#             selectinload(User.attendance),
#             with_loader_criteria(PaymentDetail, lambda p: (
#                         (p.group_id == group_id)
#                     )
#                 )
#             )
#         )
#     result = await session.execute(stmt)
#     students = result.scalars().all()
#     response = []
#     for student in students:
#         attendances = [a for a in user.attendance if a.group_id == group_id]
#         total = len(attendances)
#         present = sum(1 for a in attendances if a.status == AttendanceStatus.ATTENTED)
#         percent = round(present / total * 100, 2) if total > 0 else 0.0
#         response.append(
#             GroupStudentDetailResponse(
#                 student = StudentResponse(
#                     id=student.id,
#                     first_name=student.first_name,
#                     last_name=student.last_name
#                     )
#                 ),
#                 payment_status = student.payments[0].status,
#                 attendance_ratio = percent
#             )
#     return response



@group_students_router.get(
        '/',
        response_model=List[GroupStudentResponse],
        status_code=status.HTTP_200_OK,
)
async def group_students_list(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_teacher_user)
):
    '''
    Returns a list of group with students
    '''
    query = select(Group).offset(offset=offset).limit(limit=limit).options(
        selectinload(Group.students),
        selectinload(Group.teacher)
        )
    groups = await session.execute(query)
    return groups.scalars().all()


@group_students_router.get(
        '/{group_id}',
        response_model=GroupStudentResponse,
        status_code=status.HTTP_200_OK
        )
async def group_students_detail(
    group_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_teacher_user)
):
    '''
    Returns detailed group data with students by group id
    '''
    group = await session.get(Group, group_id, options=[
        selectinload(Group.students),
        selectinload(Group.teacher)
        ])
    if not group:
        raise HTTPException(
            detail={"detail" : "Group doesn't exists"},
                    status_code=status.HTTP_404_NOT_FOUND
                    )
    return group


@group_students_router.put(
        '/{group_id}',
        response_model=GroupStudentResponse,
        status_code=status.HTTP_200_OK
        )
async def group_students_update(
    group_id: int,
    group_update: GroupStudentUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Updates group by group id from the submitted data with students fields
    NOTE -> students fields must contains ids
    '''
    group = await session.get(Group, group_id, options=[
        selectinload(Group.students),
        selectinload(Group.teacher), selectinload(Group.course)])
    if not group:
        raise HTTPException(
            detail={"detail" : "Group doesn't exists"},
            status_code=status.HTTP_404_NOT_FOUND
            )
    old_student_ids = {student.id for student in group.students}
    result = await session.execute(select(User)
                                   .where(
                                       User.id.in_(group_update.students)
                                       )
                                    )
    students = result.scalars().all()
    if len(students) != len(group_update.students):
        raise HTTPException(
            detail={
                "detail": "The request has a user id that does not exist"
                },
                status_code=status.HTTP_400_BAD_REQUEST
                )
    new_student_ids = set(group_update.students) - old_student_ids

    for key, value in group_update.model_dump(exclude_unset=True).items():
        if key == "students":
            group.students = students
        else:
            setattr(group, key, value)

    for student_id in new_student_ids:
        await create_initial_payment(student_id, group_id, db=session)

    deleted_student_ids = old_student_ids - set(group_update.students)
    for student_id in deleted_student_ids:
        await inactivate_payment(student_id, group_id, db=session)

    await session.commit()
    await session.refresh(
        group,
        # attribute_names=['students', 'teacher']
        )
    return group


@group_students_router.patch(
        '/{group_id}',
        response_model=GroupStudentResponse,
        status_code=status.HTTP_200_OK
        )
async def group_students_partial_update(
    group_id: int,
    group_update: GroupStundentPartialUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Partial update group by group id from the submitted data with students fields
    NOTE -> students fields must contains ids
    '''
    result = await session.execute(
        select(Group)
        .options(
            selectinload(Group.students),
            selectinload(Group.teacher),
            selectinload(Group.course)
        )
        .where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            detail={"detail" : "Group doesn't exists"},
            status_code=status.HTTP_404_NOT_FOUND
            )

    old_student_ids = {student.id for student in group.students}

    result = await session.execute(select(User)
                                   .where(
                                       User.id.in_(group_update.students)
                                       )
                                    )
    students = result.scalars().all()
    if len(students) != len(group_update.students):
        raise HTTPException(
            detail={
                "detail" : "The request has a user id that does not exist"
                },
                status_code=status.HTTP_400_BAD_REQUEST
                )

    new_student_ids = set(group_update.students) - old_student_ids

    for key, value in group_update.model_dump(exclude_unset=True).items():
        if key == "students":
            group.students = students
        else:
            setattr(group, key, value)

    for student_id in new_student_ids:
        await create_initial_payment(student_id, group_id, db=session)

    deleted_student_ids = old_student_ids - set(group_update.students)
    for student_id in deleted_student_ids:
        await inactivate_payment(student_id, group_id, db=session)


    await session.commit()
    await session.refresh(
        group,
        # attribute_names=['students', 'teacher']
        )
    return group

@group_router.get(
        "/my", 
        response_model=List[GroupTeacherProfileResponse], 
        status_code=status.HTTP_200_OK
)
async def group_list_profile(
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Returns current teacher user groups

    ROLES -> teacher 
    '''
    stmt = (
        select(Group, func.count(User.id).label("student_count"))
        .options(selectinload(Group.course))
        .outerjoin(Group.students)
        .where(Group.teacher_id == user.id)
        .group_by(Group.id)
        )
    result = await session.execute(stmt)
    group_rows = result.mappings().all()
    response = []
    for row in group_rows:
        group = row['Group']
        response.append(
            GroupTeacherProfileResponse(
                id=group.id,
                name=group.name,
                start_date=group.start_date,
                end_date=group.end_date,
                is_active=group.is_active,
                student_count=row['student_count']
            )
        )
    return response

@group_router.get("/", response_model=List[GroupResponse], status_code=status.HTTP_200_OK)
async def group_list(
    limit: int = 10,
    offset: int = 0,
    user: User = Depends(optional_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Returns a list of groups
    '''
    query = select(Group).options(selectinload(Group.teacher)).offset(offset=offset).limit(limit=limit)
    groups = await session.execute(query)
    return groups.scalars().all()
    

@group_router.get(
        "/{group_id}",
        response_model=GroupResponse,
        status_code=status.HTTP_200_OK
        )
async def group_detail(
    group_id: int,
    user: User = Depends(optional_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Returns detailed group data by group id
    '''
    # query = select(student_group_association_table).where(
    #     student_group_association_table.c.group_id == group_id
    # ).options(selectinload(Group.teacher))
    # if user.role == Role.STUDENT:
    #     query = select(student_group_association_table).where(
    #         student_group_association_table.c.user_id == user.id,
    #         student_group_association_table.c.group_id == group_id
    #     )
    # result = await session.execute(query)
    # group = result.scalar_one_or_none()

    group = await session.get(Group, group_id, options=[selectinload(Group.teacher)])
    
    if not group:
        raise HTTPException(detail=
            {
                "detail":"Group does't exist or you doesn't have permission"
            },
            status_code=status.HTTP_404_NOT_FOUND
            )

    return group


    
@group_router.post(
        '/',
        response_model=GroupResponse,
        status_code=status.HTTP_201_CREATED
        )
async def group_create(
    group_data: GroupCreate,
    user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Returns a list of groups
    '''
    new_group = Group(**group_data.model_dump())
    session.add(new_group)
    await session.commit()
    await session.refresh(new_group, attribute_names=['teacher'])
    return new_group


@group_router.put(
        "/{group_id}",
        response_model=GroupResponse,
        status_code=status.HTTP_200_OK
        )
async def group_update(
    group_id: int,
    group_data: GroupUpdate,
    user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Updates a group by group id from the submitted data
    '''
    groups = await session.execute(select(Group).where(Group.id == group_id))
    group = groups.scalar_one_or_none()
    if not group:
        raise HTTPException(detail={"detail" : "group doesn't exist"},
                             status_code=status.HTTP_404_NOT_FOUND)
    for key, value in group_data.model_dump().items():
        setattr(group, key, value)
    await session.commit()
    await session.refresh(group, attribute_names=['teacher'])
    return group
    
    


@group_router.patch(
        "/{group_id}",
        response_model=GroupResponse,
        status_code=status.HTTP_200_OK
        )
async def group_partial_update(
    group_id: int,
    group_data: GroupPartialUpdate,
    user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Partial Updates a group by group id from the submitted data
    '''
    groups = await session.execute(select(Group).where(Group.id == group_id))
    group = groups.scalar_one_or_none()
    if not group:
        raise HTTPException(detail={"detail" : "group doesn't exist"},
                            status_code=status.HTTP_404_NOT_FOUND)
    for key, value in group_data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    await session.commit()
    await session.refresh(group, attribute_names=['teacher'])
    return group


@group_router.delete(
        "/{group_id}",
        status_code=status.HTTP_204_NO_CONTENT
        )
async def group_delete(
    group_id: int,
    user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Delete group by group id
    '''
    group = await session.get(Group, group_id)
    await session.delete(group)
    await session.commit()
    return
