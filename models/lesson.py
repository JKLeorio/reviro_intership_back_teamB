from datetime import datetime
from typing import List, TYPE_CHECKING
from db.dbbase import Base
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.date_time_utils import get_current_time

if TYPE_CHECKING:
    from models.group import Group


class Classroom(Base):
    __tablename__ = 'classrooms'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    lessons: Mapped[List["Lesson"]] = relationship(back_populates='classroom', cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = 'lessons'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    lesson_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lesson_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    group: Mapped["Group"] = relationship(back_populates='lessons')

    classroom_id: Mapped[int] = mapped_column(ForeignKey('classrooms.id'))
    classroom: Mapped["Classroom"] = relationship(back_populates='lessons')

    homework: Mapped[List["Homework"]] = relationship(back_populates='lesson', cascade='all, delete-orphan')


class Homework(Base):

    __tablename__ = 'homeworks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    description: Mapped[str] = mapped_column(Text)

    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id'))
    lesson: Mapped["Lesson"] = relationship(back_populates='homeworks')
