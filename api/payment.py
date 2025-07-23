from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import uuid
from fastapi import routing, Depends, HTTPException, status, Query

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.base.filter import FilterDepends

from api.auth import current_admin_user, current_user
from db.database import get_async_session
from db.dbbase import Base
from db.types import Currency, PaymentMethod, PaymentStatus, SubscriptionStatus, PaymentDetailStatus
from models import Group
from models.course import Course
from models.payment import Payment, Subscription, PaymentDetail
from models.user import User
from schemas.payment import (PaymentCreate, PaymentDetailBase, PaymentDetailUpdate,
                             PaymentDetailRead, PaymentPartialUpdate,
                             PaymentResponse, PaymentUpdate,
                             SubscriptionCreate, SubscriptionPartialUpdate,
                             SubscriptionResponse, SubscriptionUpdate)

subscription_router = routing.APIRouter()
payment_router = routing.APIRouter()
payment_details = routing.APIRouter()



class SubscriptionFilter(Filter):
    status__in: Optional[List[SubscriptionStatus]] = None
    created_at__gte: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Constants(Filter.Constants):
        model = Subscription

class PaymentFilter(Filter):
    payment_method__in: Optional[List[PaymentMethod]] = None
    payment_status__in: Optional[List[PaymentStatus]] = None
    currency__in: Optional[List[Currency]] = None
    owner_id: Optional[int] = None

    class Constants(Filter.Constants):
        model = Payment


async def validate_related_fields(models_ids: Dict[Base, int], session: AsyncSession):
    for model, m_id in models_ids.items():
        if not await session.get(model, m_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'detail':f'{model.__name__} not found'}
                )
    return


@subscription_router.get(
    '/',
    status_code=status.HTTP_200_OK,
    response_model=List[SubscriptionResponse]
)
async def subscription_list(
    limit: int = 10,
    offset: int = 0,
    subcription_filter: SubscriptionFilter = FilterDepends(SubscriptionFilter),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Returns a list of subscriptions
    you can use filters with query
    '''
    query = select(Subscription).offset(
        offset=offset
        ).limit(
            limit=limit
            ).options(
                selectinload(Subscription.owner),
                selectinload(Subscription.course),
            )
    query = subcription_filter.filter(query=query)

    subscriptions = await session.execute(query)

    return subscriptions.scalars().all()

@subscription_router.get(
    '/{subscription_uuid}',
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK
)
async def subscription_detail(
    subscription_uuid: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Returns detailed subscription data by subscription id
    '''
    subscription = await session.get(
        Subscription, 
        subscription_uuid, 
        options=[
            selectinload(Subscription.owner),
            selectinload(Subscription.course)
            ]
        )
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Subscription not found'}
            )
        
    return subscription



@subscription_router.post(
    '/',
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED
)
async def subscription_create(
    subscription_create: SubscriptionCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Creates a subscription from the submitted data
    '''
    await validate_related_fields(
        {
            Course : subscription_create.course_id,
            User : subscription_create.owner_id
        },
        session=session
    )
    subscription = Subscription(**subscription_create.model_dump())
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription, attribute_names=[
        'course',
        'owner',
    ])
    return subscription


@subscription_router.put(
    '/{subscription_uuid}',
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK
)
async def subscription_update(
    subscription_uuid: uuid.UUID,
    subscription_update: SubscriptionUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Updates a subscription by subscription id from the submitted data
    '''
    subscription = await session.get(
        Subscription, 
        subscription_uuid, 
        options=[
            selectinload(Subscription.owner),
            selectinload(Subscription.course)
            ]
        )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Subscription not found'}
            )
    
    await validate_related_fields(
        {
            Course, subscription_update.course_id
        },
        session=session
    )

    for key, value in subscription_update.model_dump().items():
        setattr(subscription, key, value)
    
    await session.commit()
    await session.refresh(subscription)
    return subscription
    
    

@subscription_router.patch(
    '/{subscription_uuid}',
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK
)
async def subscription_partial_update(
    subscription_uuid: uuid.UUID,
    subscription_update: SubscriptionPartialUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Partial updates a subscription by subscription id from the submitted data
    '''
    subscription = await session.get(
        Subscription, 
        subscription_uuid, 
        options=[
            selectinload(Subscription.owner),
            selectinload(Subscription.course)
            ]
        )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Subscription not found'}
            )
    
    await validate_related_fields(
        {
            Course, subscription_update.course_id
        },
        session=session
    )

    for key, value in subscription_update.model_dump(exclude_unset=True).items():
        setattr(subscription, key, value)
    
    await session.commit()
    await session.refresh(subscription)
    return subscription
    
    

@subscription_router.delete(
    '/{subscription_uuid}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def subscription_delete(
    subscription_uuid: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Delete subscription by subscription id
    '''
    subscription = await session.get(
        Subscription, 
        subscription_uuid, 
        options=[
            selectinload(Subscription.owner),
            selectinload(Subscription.course)
            ]
        )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Subscription not found'}
            )
    
    await session.delete(subscription)
    await session.commit()
    
    return


@payment_router.get(
    '/',
    response_model=List[PaymentResponse],
    status_code=status.HTTP_200_OK
)
async def payment_list(
    offset: int = 0,
    limit: int = 10,
    payment_filter: PaymentFilter = FilterDepends(PaymentFilter),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Returns a list of payments
    you can use filters with query
    '''    
    query = select(Payment).offset(offset=offset).limit(limit=limit).options(
        selectinload(Payment.owner),
        selectinload(Payment.subscription)
    )
    query = payment_filter.filter(query=query)
    payments = await session.execute(query)

    return payments.scalars().all()



@payment_router.get(
    '/{payment_id}',
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK
)
async def payment_detail(
    payment_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Returns detailed payment data by payment id
    '''
    payment = await session.get(
        Payment, 
        payment_id, 
        options=[
            selectinload(Payment.owner),
            selectinload(Payment.subscription)
            ]
        )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Payment not found'}
            )
    
    return payment


@payment_router.post(
    '/',
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK
)
async def payment_create(
    payment_create: PaymentCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Creates a payment from the submitted data
    '''
    await validate_related_fields(
        {
            User: payment_create.owner_id,
            Subscription: payment_create.subscription_id
        },
        session=session
    )

    payment = Payment(**payment_create.model_dump())

    session.add(payment)
    await session.commit()
    await session.refresh(payment, attribute_names=[
        'owner',
        'subscription'
    ])

    return payment


@payment_router.put(
    '/{payment_id}',
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK
)
async def payment_update(
    payment_id: int,
    payment_update: PaymentUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Updates a payment by payment id from the submitted data
    '''
    payment = await session.get(
        Payment, 
        payment_id, 
        options=[
            selectinload(Payment.owner),
            selectinload(Payment.subscription)
            ]
        )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Payment not found'}
            )
        
    for key, value in payment_update.model_dump().items():
        setattr(payment, key, value)
    
    await session.commit()
    await session.refresh(payment)
    return payment


@payment_router.patch(
    '/{payment_id}',
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK
)
async def payment_partial_update(
    payment_id: int,
    payment_update: PaymentPartialUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Partial updates a payment by payment id from the submitted data
    '''
    payment = await session.get(
        Payment, 
        payment_id, 
        options=[
            selectinload(Payment.owner),
            selectinload(Payment.subscription)
            ]
        )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Payment not found'}
            )
        
    for key, value in payment_update.model_dump(exclude_unset=True).items():
        setattr(payment, key, value)
    
    await session.commit()
    await session.refresh(payment)
    return payment

@payment_router.delete(
    '/{payment_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def payment_delete(
    payment_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    '''
    Delete payment by payment id
    '''
    payment = await session.get(
        Payment, 
        payment_id, 
        options=[
            selectinload(Payment.owner),
            selectinload(Payment.subscription)
            ]
        )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'detail': 'Payment not found'}
            )
        
    await session.delete(payment)
    await session.commit()
    return


async def create_initial_payment(
    student_id: int, group_id: int, db: AsyncSession
):
    group = await db.get(Group, group_id, options=[selectinload(Group.course)])
    exists = await db.execute(
        select(PaymentDetail).where(
            PaymentDetail.student_id == student_id,
            PaymentDetail.group_id == group_id,
        )
    )

    if exists.scalar():
        return
    joined_at = max(group.start_date, date.today())
    payment = PaymentDetail(
        student_id=student_id,
        group_id=group_id,
        joined_at=joined_at,
        price=group.course.price,
        months_paid=1,
        current_month_number=1,
        deadline=joined_at + relativedelta(months=1),
        status=PaymentDetailStatus.PAID,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def inactivate_payment(student_id: int, group_id: int, db: AsyncSession):
    result = await db.execute(
        select(PaymentDetail).where(
            PaymentDetail.student_id == student_id,
            PaymentDetail.group_id == group_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.is_active = False
        await db.commit()
        await db.refresh(payment)
        return payment
    return None


@payment_details.get("/payments", response_model=List[PaymentDetailRead], status_code=status.HTTP_200_OK)
async def get_payments_detail(group_id: Optional[int] = Query(default=None),
                              student_id: Optional[int] = Query(default=None),
                              db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_admin_user)):
    if (not group_id and not student_id) or (group_id and student_id):
        raise HTTPException(status_code=400, detail="Should provide either student_id or group_id")
    if group_id:
        group_exists = await db.execute(select(Group.id).where(Group.id == group_id))
        if not group_exists.scalars().first():
            raise HTTPException(status_code=404, detail=f"Group with id={group_id} not found")
        result = await db.execute(select(PaymentDetail).where(PaymentDetail.group_id == group_id))

    else:
        student_exists = await db.execute(select(User.id).where(User.id == student_id))
        if not student_exists.scalars().first():
            raise HTTPException(status_code=404, detail=f"Student with id={student_id} not found")
        result = await db.execute(select(PaymentDetail).where(PaymentDetail.student_id == student_id))

    return result.scalars().all()


async def update_and_check_payments():

    session_gen = get_async_session()
    session = await anext(session_gen)
    try:
        result = await session.execute(
            select(PaymentDetail)
            .options(selectinload(PaymentDetail.group))
            .where(PaymentDetail.group.has(Group.is_active.is_(True)) & PaymentDetail.is_active)
        )
        payments = result.scalars().all()
        for payment in payments:
            curr_date = payment.joined_at + relativedelta(months=payment.current_month_number)
            if curr_date <= date.today() and curr_date < payment.group.end_date:
                payment.current_month_number += 1
                payment.status = (
                    PaymentDetailStatus.UNPAID
                    if payment.current_month_number > payment.months_paid
                    else PaymentDetailStatus.PAID
                )
        await session.commit()
    finally:
        await session.close()


async def get_payment_by_id_or_pair(db: AsyncSession, payment_id: Optional[int], group_id: Optional[int],
                                    student_id: Optional[int]):
    if payment_id:
        return await db.get(PaymentDetail, payment_id)
    elif student_id and group_id:
        result = await db.execute(select(PaymentDetail).where(PaymentDetail.group_id == group_id,
                                                              PaymentDetail.student_id == student_id))
        return result.scalar_one_or_none()
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Should provide either payment_id or both student_id and group_id"
    )


@payment_details.get('/', response_model=PaymentDetailRead, status_code=status.HTTP_200_OK)
async def get_payment_detail_by_id(payment_id: Optional[int] = Query(default=None),
                                   group_id: Optional[int] = Query(default=None),
                                   student_id: Optional[int] = Query(default=None),
                                   db: AsyncSession = Depends(get_async_session),
                                   user: User = Depends(current_admin_user)):

    payment = await get_payment_by_id_or_pair(db, payment_id, group_id, student_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@payment_details.get('/my_payments', response_model=List[PaymentDetailBase], status_code=status.HTTP_200_OK)
async def my_payment_details(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    result = await db.execute(select(PaymentDetail).options(selectinload(PaymentDetail.group))
                              .where(PaymentDetail.student_id == user.id))
    payments = result.scalars().all()
    return [
        PaymentDetailBase(
            id=p.id,
            student_id=p.student_id,
            group_id=p.group_id,
            group_name=p.group.name if p.group else "",
            group_end=p.group.end_date if p.group and p.group.end_date else "",
            deadline=p.deadline,
            status=p.status
        )
        for p in payments
    ]


@payment_details.patch('/', response_model=PaymentDetailRead, status_code=status.HTTP_200_OK)
async def update_payment_by_payment_id(data: PaymentDetailUpdate,
                                       payment_id: Optional[int] = Query(default=None),
                                       group_id: Optional[int] = Query(default=None),
                                       student_id: Optional[int] = Query(default=None),
                                       db: AsyncSession = Depends(get_async_session),
                                       user: User = Depends(current_admin_user)):

    payment = await get_payment_by_id_or_pair(db, payment_id, group_id, student_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(payment, key, value)
    if payment.joined_at is not None and payment.months_paid is not None:
        payment.deadline = payment.joined_at + relativedelta(months=payment.months_paid)
    if payment.current_month_number and payment.months_paid:
        payment.status = (
            PaymentDetailStatus.UNPAID if payment.current_month_number > payment.months_paid
            else PaymentDetailStatus.PAID
        )
    await db.commit()
    await db.refresh(payment)
    return payment


@payment_details.delete('/', status_code=status.HTTP_200_OK)
async def destroy_payment_by_payment_id(payment_id: Optional[int] = Query(default=None),
                                        group_id: Optional[int] = Query(default=None),
                                        student_id: Optional[int] = Query(default=None),
                                        db: AsyncSession = Depends(get_async_session),
                                        user: User = Depends(current_admin_user)):
    payment = payment = await get_payment_by_id_or_pair(db, payment_id, group_id, student_id)
    if not payment:
        raise HTTPException(status_code=404, detail='Payment detail not found')
    await db.delete(payment)
    await db.commit()
    return {'detail': "Payment detail has been deleted"}