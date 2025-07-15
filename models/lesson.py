from datetime import date, time, datetime
from typing import List, TYPE_CHECKING, Optional

from pydantic import HttpUrl
from db.dbbase import Base
from db.types import HttpUrlType
from sqlalchemy import String, DateTime, ForeignKey, Text, Date, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.user import User
from utils.date_time_utils import get_current_time

if TYPE_CHECKING:
    from models.group import Group


class Classroom(Base):
    __tablename__ = 'classrooms'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    lessons: Mapped[List["Lesson"]] = relationship(back_populates='classroom', cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = 'lessons'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[str] = mapped_column(Text)

    link: Mapped[HttpUrl] = mapped_column(HttpUrlType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    day: Mapped[date] = mapped_column(Date, nullable=False)

    lesson_start: Mapped[time] = mapped_column(Time, nullable=False)
    lesson_end: Mapped[time] = mapped_column(Time, nullable=False)

    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    group: Mapped["Group"] = relationship(back_populates='lessons')

    classroom_id: Mapped[int] = mapped_column(ForeignKey('classrooms.id'))
    classroom: Mapped["Classroom"] = relationship(back_populates='lessons')

    teacher: Mapped["User"] = relationship(back_populates='lessons')

    homework: Mapped["Homework"] = relationship(back_populates='lesson', cascade='all, delete-orphan',
                                                passive_deletes=True)

    @property
    def group_name(self) -> str | None:
        return self.group.name if self.group else None

    @property
    def classroom_name(self) -> str | None:
        return self.classroom.name if self.classroom else None


class Homework(Base):

    __tablename__ = 'homeworks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)

    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'))
    lesson: Mapped["Lesson"] = relationship(back_populates='homework')

    submissions: Mapped[List["HomeworkSubmission"]] = relationship('HomeworkSubmission', back_populates='homework',
                                                                   lazy="selectin",
                                                                   cascade='all, delete-orphan')


class HomeworkSubmission(Base):
    __tablename__ = 'homework_submissions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey('homeworks.id', ondelete='CASCADE'))
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    homework: Mapped["Homework"] = relationship('Homework', back_populates='submissions')
    review: Mapped['HomeworkReview'] = relationship('HomeworkReview', back_populates='submission',
                                                    cascade='all, delete-orphan')
    student = relationship('User')


class HomeworkReview(Base):
    __tablename__ = 'homework_reviews'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("homework_submissions.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    submission = relationship('HomeworkSubmission', back_populates='review')
    teacher = relationship('User')
