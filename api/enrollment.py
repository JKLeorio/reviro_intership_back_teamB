from typing import List
from fastapi import Depends, routing, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import  current_admin_user, optional_current_user, current_user

from db.database import get_async_session
from db.types import Role
from models.user import User
from schemas.enrollment import EnrollmentCreate, EnrollmentResponse, EnrollmentUpdate
from models.enrollment import Enrollment
from models.course import Course

router = routing.APIRouter(prefix='/enrollment/')


# @router.get('/all', response_model=List[EnrollmentResponse])
# async def enrollment_list(
#     session: AsyncSession = Depends(get_async_session),
#     user: User = Depends(current_admin_user)
# ):
#     enrollments = await session.execute(select(Enrollment))
#     return enrollments

@router.get('/my', response_class=List[EnrollmentResponse])
async def user_enrollment(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    enrollments = await session.execute(select(Enrollment).where(User.id == user.id))
    return enrollments

@router.get('/{enrollment_id}/detail', response_model=EnrollmentResponse)
async def enrollment_detail(
    enrollment_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user)
):
    enrollment = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id)).first()
    if not enrollment:
        raise HTTPException(detail={"detail" : "enrollment doesn't exist"})
    # elif user.role == Role.ADMIN:
    #     return enrollment
    elif user.id == enrollment.user_id:
        return enrollment
    raise HTTPException(detail={"detail" : "enrollment doesn't exist or you haven't permission"})


@router.post('/create', response_model=EnrollmentResponse)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User | None = Depends(optional_current_user),
):
    new_enrollment = Enrollment(**enrollment_data.model_dump())
    session.add(new_enrollment)
    await session.commit()
    await session.refresh(new_enrollment)
    return new_enrollment


@router.put('/{enrollment_id}/update', response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    enrollment = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id)).first()
    if not enrollment:
        raise HTTPException(detail={"detail" : "enrollment doesn't exist"})
    # elif user.role == Role.ADMIN:
    #     return enrollment
    elif user.id == enrollment.user_id:
        for key, value in enrollment_data.items():
            setattr(enrollment, key, value)
        session.add(enrollment)
        await session.commit()
        await session.refresh(enrollment)
        return enrollment
    raise HTTPException(detail={"detail" : "you haven't permission"})

@router.delete('/{enrollment_id}/detail', status_code=status.HTTP_204_NO_CONTENT)
async def enrollment_detail(
    enrollment_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user)
):
    enrollment = await session.execute(select(Enrollment).where(Enrollment.id == enrollment_id)).first()
    if not enrollment:
        raise HTTPException(detail={"detail" : "enrollment doesn't exist"})
    # elif user.role == Role.ADMIN:
    #     return enrollment
    elif user.id == enrollment.user_id:
        await session.delete(enrollment)
        await session.commit()
        return {"detail" : "succesfull deleted"}
    raise HTTPException(detail={"detail" : "enrollment doesn't exist or you haven't permission"})