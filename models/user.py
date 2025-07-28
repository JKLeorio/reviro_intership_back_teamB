from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from fastapi_users.db import SQLAlchemyBaseUserTable

from utils.date_time_utils import get_current_time
from db.dbbase import Base
from db.types import Role
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.lesson import Lesson, Attendance
    from models.group import Group
    from models.payment import Payment, Subscription, PaymentDetail


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
