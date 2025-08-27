from datetime import datetime
from typing import List
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table, Enum, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
from fastapi_users.db import SQLAlchemyBaseUserTable

from utils.date_time_utils import get_current_time
from db.dbbase import Base
from db.types import OTP_purpose, Role
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.lesson import Lesson, Attendance
    from models.group import Group
    from models.payment import Payment, Subscription, PaymentDetail, PaymentCheck


student_group_association_table = Table(
    "student_group_association_table",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True)
)


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_time)

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role", create_type=False), nullable=False)
    
    description: Mapped[str] = mapped_column(
        Text, nullable=True
    )

    groups_taught: Mapped[List["Group"]] = relationship(back_populates="teacher")

    groups_joined: Mapped[List["Group"]] = relationship(
        secondary=student_group_association_table,
        back_populates="students"
    )
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="teacher")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="owner")

    payments = relationship('Payment', back_populates='owner')
    payment_details: Mapped[list["PaymentDetail"]] = relationship('PaymentDetail', back_populates='student')
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="student")

    payment_checks: Mapped[List["PaymentCheck"]] = relationship(back_populates="student", passive_deletes=True)
      
    def __str__(self):
        return f"({self.id}){self.email} <-> {self.first_name} {self.last_name}"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    


class OTP(Base):
    __tablename__ = "otps"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_time
        )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    purpose: Mapped[OTP_purpose] = mapped_column(Enum(OTP_purpose), default=OTP_purpose.UPDATE_PESONAL_DATA)
    code_hash: Mapped[str] = mapped_column(String(255))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))

    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attemps_left: Mapped[int] = mapped_column(Integer, default=5)

    __table_args__ = (
        Index("ix_otp_identifier_purpose_active", "identifier", "purpose", "active"),
        Index("ix_otp_expires", "expires_at"),
        UniqueConstraint("identifier", "purpose", "active", name="uq_otp_identifier_purpose_active"),
    )



