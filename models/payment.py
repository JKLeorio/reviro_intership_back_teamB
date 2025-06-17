from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, DateTime, ForeignKey, Integer, Enum, Float

from models.user import User
from models.course import Course
from db.dbbase import Base
from db.types import SubscriptionStatus, PaymentMethod, PaymentStatus, Currency
from utils.date_time_utils import get_current_time


class Subscription(Base):
    __table__ = "subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #Временно cascade
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    #Временно cascade
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)

    course: Mapped["Course"] = relationship(back_populates="subscriptions")
    owner: Mapped["User"] = relationship(back_populates="subcriptions")

    payments: Mapped[list["Payment"]] = relationship(back_populates="subcription")


class Payment(Base):
    __table__ = "Payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    #Временно cascade
    created_ad: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), default=Currency.KGS)
    #Временно cascade
    subcription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    subcription: Mapped["Subscription"] = relationship(back_populates="payments")
    owner: Mapped["User"] = relationship(back_populates="payments")






