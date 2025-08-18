from datetime import datetime, date
from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict

from db.types import Currency, PaymentMethod, PaymentStatus, SubscriptionStatus, PaymentDetailStatus
from models.payment import Payment, Subscription
from schemas.course import CourseRelationBase
from schemas.user import UserBase
from schemas.group import GroupBase


class SubscriptionBase(BaseModel):
    id: uuid.UUID
    created_at: datetime
    status: SubscriptionStatus
    course_id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
    

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

    model_config = ConfigDict(from_attributes=True)


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


class PaymentDetailBase(BaseModel):
    id: int
    student_id: int
    group_id: int
    deadline: date
    status: PaymentDetailStatus

    group: GroupBase
    student: UserBase

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailCreate(PaymentDetailBase):
    pass


class PaymentDetailUpdate(BaseModel):

    current_month_number: Optional[int] = None
    months_paid: Optional[int] = None
    status: Optional[PaymentDetailStatus] = None


class PaymentDetailRead(BaseModel):
    id: int
    student_id: int
    group_id: int
    joined_at: date
    months_paid: int
    is_active: bool
    price: float
    current_month_number: int
    deadline: date
    status: PaymentDetailStatus

    group: GroupBase
    student: UserBase

    model_config = ConfigDict(from_attributes=True)


class PaymentRequisiteRead(BaseModel):
    id: int
    bank_name: Optional[str] = None
    account: Optional[str] = None
    qr: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentRequisiteCreate(BaseModel):
    bank_name: str
    account: str
    qr: str


class PaymentRequisiteUpdate(BaseModel):
    bank_name: Optional[str] = None
    account: Optional[str] = None
    qr: Optional[str] = None


class PaymentCheckRead(BaseModel):
    id: int
    check: str
    student_id: Optional[int] = None
    group_id: int | None
    uploaded_at: datetime

    group: GroupBase
    student: UserBase

    model_config = ConfigDict(from_attributes=True)


class PaymentCheckShort(BaseModel):
    id: int
    check: str
    student_id: Optional[int] = None
    group_id: Optional[int] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentShort(BaseModel):
    id: int
    check: str
    student_id: Optional[int] = None
    group_id: Optional[int] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentCheckCreate(BaseModel):
    check: str
    group_id: int

    model_config = ConfigDict(from_attributes=True)


class FinanceRow(BaseModel):
    student_id: int
    student_first_name: str
    student_last_name: str
    group_id: int
    payment_detail_id: int | None
    months_paid: int | None
    current_month_number: int | None

    group: GroupBase
    checks: List[PaymentCheckShort]

    group_course_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
