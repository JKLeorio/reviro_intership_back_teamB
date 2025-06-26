from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, ForeignKey, Integer, Enum, Float, UUID

from db.dbbase import Base
from db.types import PaymentMethod, PaymentStatus, Currency, SubscriptionStatus
from utils.date_time_utils import get_current_time


if TYPE_CHECKING:
    # from models.group import Group
    from models.user import User
    from models.course import Course


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    #Временно cascade
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    #Временно cascade
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    course: Mapped["Course"] = relationship(back_populates="subscriptions")
    owner: Mapped["User"] = relationship(back_populates="subscriptions")

    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")



class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    #Временно cascade

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)
    payment_method: Mapped["PaymentMethod"] = mapped_column(
        Enum(PaymentMethod, name="paymentmethod", create_type=False), nullable=False)
    payment_status: Mapped["PaymentStatus"] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus", create_type=False), nullable=False)
    currency: Mapped["Currency"] = mapped_column(
        Enum(Currency, name="currency", create_type=False), default=Currency.KGS)

    #Временно cascade
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"))
    subscription: Mapped["Subscription"] = relationship(back_populates="payments")
    
    # group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    # group: Mapped["Group"] = relationship(back_populates="payments")

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    owner: Mapped["User"] = relationship(back_populates="payments")
