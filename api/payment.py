from datetime import datetime
from typing import Dict, List, Optional
import uuid
from fastapi import routing, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.base.filter import FilterDepends

from db.dbbase import Base
from db.types import Currency, PaymentMethod, PaymentStatus, SubscriptionStatus
from models.course import Course
from models.payment import Payment, Subscription
from models.user import User

from api.auth import current_admin_user

from db.database import get_async_session

from schemas.payment import (
    PaymentResponse, 
    PaymentCreate,
    PaymentUpdate,
    PaymentPartialUpdate,
    SubscriptionResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionPartialUpdate
    )


subscription_router = routing.APIRouter()
payment_router = routing.APIRouter()



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
async def subscription_create(
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
async def subscription_create(
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
async def subscription_create(
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