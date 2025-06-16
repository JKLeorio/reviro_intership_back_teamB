from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from fastapi_users.db import SQLAlchemyBaseUserTable

from utils.date_time_utils import get_current_time
from db.dbbase import Base
from db.types import Role
from models.group import Group


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
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_time)

    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)

    groups_taught: Mapped[List["Group"]] = relationship(back_populates="teacher")

    groups_joined: Mapped[List["Group"]] = relationship(
        secondary=student_group_association_table,
        back_populates="students"
    )
