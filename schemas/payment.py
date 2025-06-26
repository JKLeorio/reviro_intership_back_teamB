from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel

from db.types import Currency, PaymentMethod, PaymentStatus, SubscriptionStatus
from models.payment import Payment, Subscription
from schemas.course import CourseRelationBase
from schemas.user import UserBase


class SubscriptionBase(BaseModel):
    id: uuid.UUID
    created_at: datetime
    status: SubscriptionStatus
    course_id: int
    owner_id: int

    class Config:
        from_attributes = True
    

class SubscriptionResponse(SubscriptionBase):
    # course: CourseBase
    course: CourseRelationBase
    owner: UserBase
    # payments: "PaymentBase"



class SubscriptionCreate(BaseModel):
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    course_id: int
    owner_id: int


class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    course_id: int


class SubscriptionPartialUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    course_id: Optional[int] = None



class PaymentBase(BaseModel):
    id: int
    amount: float
    created_at: datetime
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    currency: Currency
    subscription: int
    owner: int

    class Config:
        from_attributes = True


class PaymentResponse(PaymentBase):
    subscription: SubscriptionBase
    owner: UserBase
    


class PaymentCreate(BaseModel):
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    payment_status: PaymentStatus = PaymentStatus.PENDING
    currency: Currency = Currency.KGS
    subscription_id: uuid.UUID
    owner_id: int


class PaymentUpdate(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.CASH
    payment_status: PaymentStatus = PaymentStatus.PENDING


class PaymentPartialUpdate(BaseModel):
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None


SubscriptionResponse.model_rebuild()