from typing import List
from fastapi import Depends, routing, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import current_admin_user, optional_current_user, current_user, current_student_user
from api.utils import validate_related_fields

from db.database import get_async_session
from db.types import Role
from models.user import User
# from schemas.enrollment import EnrollmentCreate, EnrollmentPartialUpdate, EnrollmentResponse, EnrollmentUpdate
# from models.enrollment import Enrollment
from models.course import Course

enrollment_router = routing.APIRouter()


# async def enrollment_relates(enrollment_data, session):
#     relates = {}
#     if enrollment_data.course_id is not None:
#         relates[Course] = enrollment_data.course_id
#     if 'user_id' in enrollment_data.model_fields_set:
#         if enrollment_data.user_id is not None:
#             relates[User] = enrollment_data.user_id
#     if relates:
#         await validate_related_fields(relates, session)


# @enrollment_router.get(
#         '/', 
#         response_model=List[EnrollmentResponse]
#         )
# async def enrollment_list(
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_admin_user)
# ):
#     '''
#     Returns a list of enrollments
#     '''
#     enrollments = await session.execute(select(Enrollment))
#     return enrollments.scalars().all()

# @enrollment_router.get(
#         '/my', 
#         response_model=List[EnrollmentResponse], 
#         status_code=status.HTTP_200_OK
#         )
# async def user_enrollments(
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_user)
# ):
#     '''
#     Returns list of enrollments for the current user
#     '''
#     enrollments = await session.execute(select(Enrollment).where(Enrollment.user_id == user.id))
#     return enrollments.scalars().all()

# @enrollment_router.get(
#         '/{enrollment_id}', 
#         response_model=EnrollmentResponse, 
#         status_code=status.HTTP_200_OK
#         )
# async def enrollment_detail(
#     enrollment_id: int,
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_user)
# ):
#     '''
#     Returns detailed enrollment data by enrollment id
#     '''
#     result = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
#     enrollment = result.scalars().first()
#     if not enrollment:
#         raise HTTPException(detail={"detail" : "enrollment doesn't exist"}, status_code=status.HTTP_404_NOT_FOUND)
#     elif user.role == Role.ADMIN:
#         return enrollment
#     elif user.id == enrollment.user_id:
#         return enrollment
#     raise HTTPException(detail={"detail" : "you haven't permission"}, status_code=status.HTTP_403_FORBIDDEN)


# @enrollment_router.post(
#         '/', 
#         response_model=EnrollmentResponse, 
#         status_code=status.HTTP_201_CREATED
#         )
# async def enrollment_create(
#     enrollment_data: EnrollmentCreate,
#     session: AsyncSession = Depends(get_async_session),
#     user: User | None = Depends(optional_current_user),
# ):
#     '''
#     Creates a enrollment from the submitted data
#     '''
#     await enrollment_relates(enrollment_data, session)

#     new_enrollment = Enrollment(**enrollment_data.model_dump())
#     session.add(new_enrollment)
#     await session.commit()
#     await session.refresh(new_enrollment)
#     return new_enrollment


# @enrollment_router.put(
#         '/{enrollment_id}', 
#         response_model=EnrollmentResponse, 
#         status_code=status.HTTP_200_OK
#         )
# async def enrollment_update(
#     enrollment_id: int,
#     enrollment_data: EnrollmentUpdate,
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_admin_user),
# ):
#     result = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
#     enrollment = result.scalars().first()
#     '''
#     Updates a enrollment by enrollment id from the submitted data
#     '''

#     if not enrollment:
#         raise HTTPException(detail={"detail" : "enrollment doesn't exist"}, status_code=status.HTTP_404_NOT_FOUND)
#     await enrollment_relates(enrollment_data, session)
#     if user.role != Role.ADMIN and user.id != enrollment.user_id:
#         raise HTTPException(
#                 detail={"detail": "You don't have permission"},
#                 status_code=status.HTTP_403_FORBIDDEN
#             )
#     for key, value in enrollment_data.model_dump().items():
#         setattr(enrollment, key, value)
#     await session.commit()
#     await session.refresh(enrollment)
#     return enrollment


# @enrollment_router.patch(
#         '/{enrollment_id}',
#         response_model=EnrollmentResponse, 
#         status_code=status.HTTP_200_OK
#         )
# async def enrollment_partial_update(
#     enrollment_id: int,
#     enrollment_data: EnrollmentPartialUpdate,
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_student_user),
# ):
#     '''
#     Partial Updates a enrollment by enrollment id from the submitted data
#     '''
#     result = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
#     enrollment = result.scalars().first()

#     if not enrollment:
#         raise HTTPException(detail={"detail" : "enrollment doesn't exist"}, status_code=status.HTTP_404_NOT_FOUND)
#     if user.role != Role.ADMIN and user.id != enrollment.user_id:
#         raise HTTPException(
#             detail={"detail": "You don't have permission"},
#             status_code=status.HTTP_403_FORBIDDEN
#         )
#     await enrollment_relates(enrollment_data, session)
#     for key, value in enrollment_data.model_dump(exclude_unset=True).items():
#         setattr(enrollment, key, value)
#     await session.commit()
#     await session.refresh(enrollment)
#     return enrollment


# @enrollment_router.delete(
#         '/{enrollment_id}', 
#         status_code=status.HTTP_204_NO_CONTENT
#         )
# async def enrollment_delete(
#     enrollment_id: int,
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_admin_user)
# ):
#     '''
#     Delete enrollment by enrollment id
#     '''
#     result = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
#     enrollment = result.scalars().first()

#     if not enrollment:
#         raise HTTPException(detail={"detail" : "enrollment doesn't exist"}, status_code=status.HTTP_404_NOT_FOUND)
#     elif user.role == Role.ADMIN or user.id == enrollment.user_id:
#         await session.delete(enrollment)
#         await session.commit()
#         return
#     raise HTTPException(detail={"detail" : "you haven't permission"}, status_code=status.HTTP_403_FORBIDDEN)
