from math import ceil
from typing import Annotated, List, Optional, Union
from fastapi import Query, routing, HTTPException, Depends, status

from sqlalchemy import func, select
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
from schemas.group import GroupShort, StudentWithGroupResponse, StudentWithGroupAndPagination
from schemas.course import CourseShortResponse, ProfileCourse
from schemas.pagination import Pagination
from schemas.user import (
    StudentProfile,
    TeacherFullNameResponse,
    TeacherProfile,
    TeacherWithCourseResponse,
    TeachersWithCourseAndPagination,
    UserBase,
    UserFullNameUpdate,
    UserFullnameResponse,
    UserPartialUpdate,
    UserResponse,
    UserUpdate
)

user_router = routing.APIRouter()


async def is_email_exist(email: str, session: AsyncSession) -> None:
    if (await session.execute(select(User).where(User.email == email))).scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='user with this email is already exists'
        )

async def is_phone_exist(phone_number: str, session: AsyncSession) -> None:
    if (await session.execute(select(User).where(User.phone_number == phone_number))).scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='user with this email is already exists'
        )
    
async def validate_user_unique(email: str, phone_number: str, session) -> None:
    await is_email_exist(email, session)
    await is_phone_exist(phone_number, session)


class UserFilter(Filter):
    role__in: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = User


@user_router.get(
    '/teachers',
    response_model=TeachersWithCourseAndPagination,
    status_code=status.HTTP_200_OK
)
async def teacher_list(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    course_id: Annotated[int | None, Query()] = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    """
    Return teachers with courses
    ROLES -> admin

    has pagination and filtration by course
    """
    offset = (page-1)*size
    stmt = (
        select(User)
        .options(
            selectinload(User.groups_taught)
            .options(selectinload(Group.course))
        )
        .join(User.groups_taught, isouter=True)
        .where(
            User.role == Role.TEACHER,
        )
        .distinct(User.id)
        .offset(offset=offset)
        .limit(limit=size)
    )
    if course_id is not None:
        stmt = stmt.where(Group.course_id == course_id)
        
    stmt_total = (
        select(func.count())
        .select_from(User)
        .where(
            User.role == Role.TEACHER
        )
    )
    result = await session.execute(stmt)
    teachers = result.scalars().all()
    total_items = (await session.execute(stmt_total)).scalar_one()
    total_pages = ceil(total_items / size) if total_items else 1

    if page > total_pages:
        page = total_pages

    response_teachers = [
        TeacherWithCourseResponse(
        id=teacher.id,
        full_name=teacher.full_name,
        email=teacher.email,
        phone_number=teacher.phone_number,
        role=teacher.role,
        is_active=teacher.is_active,
        courses=[
            CourseShortResponse.model_validate(
                group.course,
                from_attributes=True
            ) for group in teacher.groups_taught
        ]
        ) for teacher in teachers
    ]
    response = TeachersWithCourseAndPagination(
        teachers=response_teachers,
        pagination=Pagination(
            current_page_size=size,
            current_page=page,
            total_pages=total_pages
        )
    )
    return response

@user_router.get(
    '/students',
    response_model=StudentWithGroupAndPagination,
    status_code=status.HTTP_200_OK
)
async def student_list(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    group_id: Annotated[int | None, Query()] = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    """
    Return students with courses
    ROLES -> admin

    has pagination and filtration by course
    """
    offset = (page-1)*size
    stmt = (
        select(User)
        .options(
            selectinload(User.groups_joined)
        )
        .join(User.groups_joined)
        .where(
            User.role == Role.STUDENT,
        )
        .distinct(User.id)
        .offset(offset=offset)
        .limit(limit=size)
    )
    if group_id is not None:
        stmt = stmt.where(Group.id == group_id)
    
    stmt_total = (
        select(func.count())
        .select_from(User)
        .where(
            User.role == Role.STUDENT
        )
    )
    result = await session.execute(stmt)
    students = result.scalars().all()
    total_items = (await session.execute(stmt_total)).scalar_one()
    total_pages = ceil(total_items / size) if total_items else 1

    if page > total_pages:
        page = total_pages

    response_students = [
        StudentWithGroupResponse(
        id=student.id,
        full_name=student.full_name,
        email=student.email,
        phone_number=student.phone_number,
        role=student.role,
        is_active=student.is_active,
        groups=[
            GroupShort.model_validate(
                group,
                from_attributes=True
            ) for group in student.groups_joined
        ]
        ) for student in students
    ]
    response = StudentWithGroupAndPagination(
        students=response_students,
        pagination=Pagination(
            current_page_size=size,
            current_page=page,
            total_pages=total_pages
        )
    )
    return response



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

@user_router.patch(
    '/student/{student_id}',
    response_model=UserFullnameResponse,
    status_code=status.HTTP_200_OK
)
async def student_partial_update(
    student_id: int,
    student_data: UserFullNameUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Partial update student personal data
    student_id: integer -> user id
    ROLES -> admin
    """
    try:
        user_to_update = await user_manager.get(student_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='student not found'
            )
    if user_to_update.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='student not found'
            )
    await validate_user_unique(
        email=student_data.email,
        phone_number=student_data.phone_number,
        session=session
        )
    student_data = UserPartialUpdate(**student_data.model_dump(exclude_none=True))
    updated_user = await user_manager.update(student_data, user_to_update)
    return UserFullnameResponse.model_validate(updated_user)



@user_router.patch(
    '/teacher/{teacher_id}',
    response_model=TeacherFullNameResponse,
    status_code=status.HTTP_200_OK
)
async def teacher_partial_update(
    teacher_id: int,
    teacher_data: UserFullNameUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Partial update teacher personal data
    teacher_id: integer -> user id
    ROLES -> admin
    """
    try:
        user_to_update = await user_manager.get(teacher_id)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='teacher not found'
            )
    if user_to_update.role != Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='teacher not found'
            )
    await validate_user_unique(
        email=teacher_data.email,
        phone_number=teacher_data.phone_number,
        session=session
        )
    teacher_data = UserPartialUpdate(**teacher_data.model_dump(exclude_none=True))
    updated_user = await user_manager.update(teacher_data, user_to_update)
    return TeacherFullNameResponse.model_validate(updated_user)

    


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
    session: AsyncSession = Depends(get_async_session),
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
    await validate_user_unique(
        email=user_update.email,
        phone_number=user_update.phone_number,
        session=session
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
    session: AsyncSession = Depends(get_async_session),
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
    await validate_user_unique(
        email=user_update.email,
        phone_number=user_update.phone_number,
        session=session
        )
    teacher_data = UserPartialUpdate(teacher_data.model_dump(exclude_none=True))
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


#Временно, костыль для избежания циркулярного импорта
class TeacherCourseGroupResponse(TeacherFullNameResponse):
    groups: list[GroupShort]
    courses: list[CourseShortResponse]

class StudentCourseGroupResponse(UserFullnameResponse):
    groups: list[GroupShort]
    courses: list[CourseShortResponse]


@user_router.get(
    '/teacher/{user_id}',
    response_model=TeacherCourseGroupResponse,
    status_code=status.HTTP_200_OK
)
async def get_teacher_detail_profile_data(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)  
):
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.groups_taught)
            .selectinload(Group.course)
        )
    )
    result = await session.execute(stmt)
    teacher = result.scalar_one_or_none()
    if (teacher is None) or (teacher.role != Role.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Teacher not found'
        )
    
    groups = [
        GroupShort.model_validate(group, from_attributes=True) 
        for group in teacher.groups_taught
        ]
    courses = {
        group.course for group in teacher.groups_taught
        }
    courses = [
        CourseShortResponse.model_validate(course, from_attributes=True)
        for course in courses
        ]
    response = TeacherCourseGroupResponse(
        id=teacher.id,
        full_name=teacher.full_name,
        email=teacher.email,
        phone_number=teacher.phone_number,
        role=teacher.role,
        is_active=teacher.is_active,
        description=teacher.description,
        groups=groups,
        courses=courses
    )
    return response
    



@user_router.get(
    '/student/{user_id}',
    response_model=StudentCourseGroupResponse,
    status_code=status.HTTP_200_OK
)
async def get_teacher_detail_profile_data(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)  
):
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.groups_joined)
            .selectinload(Group.course)
        )
    )
    result = await session.execute(stmt)
    student = result.scalar_one_or_none()
    if (student is None) or (student.role != Role.STUDENT):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Student not found'
        )
    
    groups = [
        GroupShort.model_validate(group, from_attributes=True) 
        for group in student.groups_joined
        ]
    courses = {
        group.course for group in student.groups_joined
        }
    courses = [
        CourseShortResponse.model_validate(course, from_attributes=True)
        for course in courses
        ]
    response = StudentCourseGroupResponse(
        id=student.id,
        full_name=student.full_name,
        email=student.email,
        phone_number=student.phone_number,
        role=student.role,
        is_active=student.is_active,
        groups=groups,
        courses=courses
    )
    return response