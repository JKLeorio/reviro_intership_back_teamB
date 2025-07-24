from typing import List
from fastapi import routing, HTTPException, Depends, status

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_session
from api.auth import (
    optional_current_user,
    current_user,
    current_student_user,
    current_teacher_user,
    current_admin_user
    )
from db.types import Role
from models.user import User, student_group_association_table
from models.group import Group
from models.course import Course
from schemas.group import (
    GroupCreate,
    GroupProfileResponse, 
    GroupResponse,
    GroupStundentPartialUpdate, 
    GroupUpdate, 
    GroupPartialUpdate,
    GroupStudentResponse,
    GroupStudentUpdate
    )


group_router = routing.APIRouter()

#Удаление студента из группы, добавление в группу и т.д
group_students_router = routing.APIRouter()


@group_students_router.get(
        "/my", 
        response_model=List[GroupProfileResponse], 
        status_code=status.HTTP_200_OK
)
async def group_list_profile(
    user: User = Depends(current_teacher_user),
    session: AsyncSession = Depends(get_async_session)
):
    '''
    Returns current user groups

    ROLES -> student 
    '''
    stmt = (
        select(Group, func.count(User.id).label("student_count"))
        .options(selectinload(Group.course))
        .outerjoin(Group.students)
        .where(Group.students.any(User.id == user.id))
        .group_by(Group.id)
        )

    result = await session.execute(stmt)
    group_rows = result.mappings().all()
    response = []
    for row in group_rows:
        group = row['Group']
        response.append(
            GroupProfileResponse(
                id=group.id,
                name=group.name,
                start_date=group.start_date,
                end_date=group.end_date,
                is_active=group.is_active,
                student_count=row['student_count']
            )
        )
    return response

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
        selectinload(Group.teacher)])
    if not group:
        raise HTTPException(
            detail={"detail" : "Group doesn't exists"},
            status_code=status.HTTP_404_NOT_FOUND
            )
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
    
    print(group_update.model_dump())
    for key, value in group_update.model_dump(exclude_unset=True).items():
        if key == "students":
            group.students = students
        else:
            setattr(group, key, value)

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
    group = await session.get(Group, group_id, options=[
        selectinload(Group.students),
        selectinload(Group.teacher)])
    if not group:
        raise HTTPException(
            detail={"detail" : "Group doesn't exists"},
            status_code=status.HTTP_404_NOT_FOUND
            )
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
    
    for key, value in group_update.model_dump(exclude_unset=True).items():
        if key == "students":
            group.students = students
        else:
            setattr(group, key, value)


    await session.commit()
    await session.refresh(
        group,
        # attribute_names=['students', 'teacher']
        )
    return group




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

    
